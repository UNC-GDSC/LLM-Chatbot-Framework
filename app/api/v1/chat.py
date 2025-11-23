"""Chat endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationCreate,
    ConversationUpdate,
    MessageResponse,
    ModelConfig,
)
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Send a chat message and get response."""
    chat_service = ChatService(db)

    try:
        conversation, message = await chat_service.process_chat_message(user_id, request)

        model_config = request.model_config or ModelConfig()
        if conversation.model_config:
            model_config = ModelConfig(**conversation.model_config)

        return ChatResponse(
            conversation_id=conversation.id,
            message=MessageResponse.from_orm(message),
            model_config=model_config,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
        )


@router.websocket("/stream")
async def stream_message(websocket: WebSocket) -> None:
    """Stream chat responses via WebSocket."""
    await websocket.accept()

    try:
        # Receive authentication token
        auth_data = await websocket.receive_json()
        token = auth_data.get("token")

        if not token:
            await websocket.send_json({"error": "Authentication required"})
            await websocket.close()
            return

        # Verify token and get user_id
        from app.core.security import decode_token
        try:
            payload = decode_token(token)
            user_id = payload.get("sub")
        except Exception:
            await websocket.send_json({"error": "Invalid token"})
            await websocket.close()
            return

        # Get database session
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            chat_service = ChatService(db)
            llm_service = LLMService()

            # Receive chat request
            while True:
                data = await websocket.receive_json()

                conversation_id = data.get("conversation_id")
                message = data.get("message")
                model_config_data = data.get("model_config", {})
                model_config = ModelConfig(**model_config_data)

                if not message:
                    await websocket.send_json({"error": "Message required"})
                    continue

                # Create or get conversation
                if conversation_id:
                    conversation = await chat_service.get_conversation(conversation_id, user_id)
                    if not conversation:
                        await websocket.send_json({"error": "Conversation not found"})
                        continue
                else:
                    title = message[:50] + "..." if len(message) > 50 else message
                    conversation = await chat_service.create_conversation(
                        user_id,
                        ConversationCreate(title=title, model_config=model_config),
                    )

                # Add user message
                await chat_service.add_message(conversation.id, "user", message)

                # Get conversation history
                history = await chat_service.get_conversation_history(conversation.id)

                # Send conversation_id to client
                await websocket.send_json({
                    "type": "conversation_id",
                    "conversation_id": conversation.id,
                })

                # Stream response
                full_response = ""
                async for chunk in llm_service.generate_stream(history, model_config):
                    full_response += chunk
                    await websocket.send_json({
                        "type": "chunk",
                        "content": chunk,
                    })

                # Save assistant response
                await chat_service.add_message(conversation.id, "assistant", full_response)

                # Send completion
                await websocket.send_json({"type": "complete"})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Create a new conversation."""
    chat_service = ChatService(db)
    conversation = await chat_service.create_conversation(user_id, data)

    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=0,
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[ConversationResponse]:
    """Get user's conversations."""
    chat_service = ChatService(db)
    conversations = await chat_service.get_user_conversations(user_id, limit, offset)

    return [
        ConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.messages) if hasattr(conv, 'messages') else 0,
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Get a specific conversation with messages."""
    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = [MessageResponse.from_orm(msg) for msg in conversation.messages]

    return ConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=len(messages),
        messages=messages,
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Update conversation title."""
    chat_service = ChatService(db)

    if data.title:
        conversation = await chat_service.update_conversation_title(
            conversation_id, user_id, data.title
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

        return ConversationResponse(
            id=conversation.id,
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=len(conversation.messages) if hasattr(conversation, 'messages') else 0,
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No fields to update",
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a conversation."""
    chat_service = ChatService(db)
    deleted = await chat_service.delete_conversation(conversation_id, user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
