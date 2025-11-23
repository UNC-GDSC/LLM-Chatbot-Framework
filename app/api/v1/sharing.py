"""Conversation sharing endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.services.sharing_service import SharingService
from app.services.chat_service import ChatService
from app.schemas.chat import ConversationResponse, MessageResponse

router = APIRouter()


class ShareRequest(BaseModel):
    """Request schema for creating a share link."""

    conversation_id: str
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)


class ShareResponse(BaseModel):
    """Response schema for share link."""

    id: str
    conversation_id: str
    share_token: str
    share_url: str
    expires_at: Optional[str] = None
    view_count: int
    is_active: bool


@router.post("/create", response_model=ShareResponse, status_code=status.HTTP_201_CREATED)
async def create_share_link(
    request: ShareRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ShareResponse:
    """Create a shareable link for a conversation."""
    if not settings.ENABLE_CONVERSATION_SHARING:
        raise HTTPException(status_code=403, detail="Conversation sharing disabled")

    # Verify user owns the conversation
    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(request.conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    sharing_service = SharingService(db)
    shared = await sharing_service.create_share_link(
        request.conversation_id,
        user_id,
        request.expires_in_days,
    )

    return ShareResponse(
        id=shared.id,
        conversation_id=shared.conversation_id,
        share_token=shared.share_token,
        share_url=f"/api/v1/sharing/view/{shared.share_token}",
        expires_at=shared.expires_at.isoformat() if shared.expires_at else None,
        view_count=shared.view_count,
        is_active=shared.is_active,
    )


@router.get("/view/{share_token}", response_model=ConversationResponse)
async def view_shared_conversation(
    share_token: str,
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """View a shared conversation (no authentication required)."""
    if not settings.ENABLE_CONVERSATION_SHARING:
        raise HTTPException(status_code=403, detail="Conversation sharing disabled")

    sharing_service = SharingService(db)
    conversation = await sharing_service.get_shared_conversation(share_token)

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Shared conversation not found or link expired",
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


@router.delete("/{share_token}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    share_token: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke a share link."""
    sharing_service = SharingService(db)
    revoked = await sharing_service.revoke_share_link(share_token, user_id)

    if not revoked:
        raise HTTPException(status_code=404, detail="Share link not found")


@router.get("/conversation/{conversation_id}", response_model=List[ShareResponse])
async def get_conversation_shares(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[ShareResponse]:
    """Get all share links for a conversation."""
    sharing_service = SharingService(db)
    shares = await sharing_service.get_conversation_shares(conversation_id, user_id)

    return [
        ShareResponse(
            id=share.id,
            conversation_id=share.conversation_id,
            share_token=share.share_token,
            share_url=f"/api/v1/sharing/view/{share.share_token}",
            expires_at=share.expires_at.isoformat() if share.expires_at else None,
            view_count=share.view_count,
            is_active=share.is_active,
        )
        for share in shares
    ]
