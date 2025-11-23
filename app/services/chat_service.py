"""Chat service for managing conversations and messages."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message
from app.schemas.chat import ChatRequest, ModelConfig, ConversationCreate
from app.services.llm_service import LLMService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """Service for managing chat conversations and messages."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize chat service."""
        self.db = db
        self.llm_service = LLMService()

    async def create_conversation(
        self, user_id: str, data: ConversationCreate
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=data.title,
            model_config=data.model_config.dict() if data.model_config else None,
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation

    async def get_conversation(
        self, conversation_id: str, user_id: str
    ) -> Optional[Conversation]:
        """Get a conversation by ID."""
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> List[Conversation]:
        """Get all conversations for a user."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        result = await self.db.execute(
            delete(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user_id
            )
        )
        await self.db.commit()
        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted conversation {conversation_id}")
        return deleted

    async def add_message(
        self, conversation_id: str, role: str, content: str, tokens: Optional[int] = None
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            tokens=tokens,
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message

    async def get_conversation_history(
        self, conversation_id: str
    ) -> List[dict]:
        """Get conversation history in format suitable for LLM."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(settings.MAX_CONVERSATION_HISTORY)
        )
        messages = result.scalars().all()

        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def process_chat_message(
        self, user_id: str, request: ChatRequest
    ) -> tuple[Conversation, Message]:
        """Process a chat message and generate response."""
        # Get or create conversation
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            # Create new conversation with first message as title
            title = request.message[:50] + "..." if len(request.message) > 50 else request.message
            conversation = await self.create_conversation(
                user_id,
                ConversationCreate(
                    title=title,
                    model_config=request.model_config
                ),
            )

        # Get model config
        model_config = request.model_config or ModelConfig()
        if conversation.model_config and not request.model_config:
            model_config = ModelConfig(**conversation.model_config)

        # Add user message to conversation
        user_message = await self.add_message(
            conversation.id, "user", request.message
        )

        # Get conversation history
        history = await self.get_conversation_history(conversation.id)

        # Generate response
        try:
            response_content = await self.llm_service.generate_response(
                history, model_config
            )

            # Add assistant message
            assistant_message = await self.add_message(
                conversation.id, "assistant", response_content
            )

            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            await self.db.commit()

            return conversation, assistant_message

        except Exception as e:
            logger.error(f"Error processing chat message: {str(e)}")
            raise

    async def update_conversation_title(
        self, conversation_id: str, user_id: str, title: str
    ) -> Optional[Conversation]:
        """Update conversation title."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None

        conversation.title = title
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation
