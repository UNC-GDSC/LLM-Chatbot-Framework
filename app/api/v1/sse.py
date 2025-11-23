"""Server-Sent Events (SSE) streaming endpoint for real-time chat."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import json
import asyncio

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService
from app.schemas.chat import ModelConfig, ConversationCreate

router = APIRouter()


class SSEChatRequest(BaseModel):
    """Request schema for SSE chat."""

    message: str
    conversation_id: str | None = None
    model_config: ModelConfig | None = None


@router.post("/chat")
async def sse_chat_stream(
    request: SSEChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Stream chat responses using Server-Sent Events."""

    async def event_generator():
        """Generate SSE events."""
        try:
            chat_service = ChatService(db)
            llm_service = LLMService()

            # Get or create conversation
            if request.conversation_id:
                conversation = await chat_service.get_conversation(
                    request.conversation_id, user_id
                )
                if not conversation:
                    yield f"event: error\ndata: {json.dumps({'error': 'Conversation not found'})}\n\n"
                    return
            else:
                title = request.message[:50] + "..." if len(request.message) > 50 else request.message
                conversation = await chat_service.create_conversation(
                    user_id,
                    ConversationCreate(title=title, model_config=request.model_config),
                )

            # Send conversation ID
            yield f"event: conversation_id\ndata: {json.dumps({'conversation_id': conversation.id})}\n\n"

            # Add user message
            await chat_service.add_message(conversation.id, "user", request.message)

            # Get conversation history
            history = await chat_service.get_conversation_history(conversation.id)

            # Get model config
            model_config = request.model_config or ModelConfig()
            if conversation.model_config and not request.model_config:
                model_config = ModelConfig(**conversation.model_config)

            # Stream response
            full_response = ""
            async for chunk in llm_service.generate_stream(history, model_config):
                full_response += chunk
                yield f"event: message\ndata: {json.dumps({'content': chunk})}\n\n"
                await asyncio.sleep(0.01)  # Small delay to prevent overwhelming

            # Save assistant response
            await chat_service.add_message(conversation.id, "assistant", full_response)

            # Send completion event
            yield f"event: done\ndata: {json.dumps({'message': 'Stream complete'})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        },
    )
