"""Webhooks API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, HttpUrl, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.webhook_service import WebhookService

router = APIRouter()


class WebhookCreate(BaseModel):
    """Request schema for creating a webhook."""

    url: HttpUrl
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = Field(None, min_length=10, max_length=100)


class WebhookResponse(BaseModel):
    """Response schema for webhook."""

    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/events")
async def list_supported_events():
    """Get list of supported webhook events."""
    return {
        "events": WebhookService.SUPPORTED_EVENTS,
        "descriptions": {
            "message.created": "Triggered when a new message is created",
            "conversation.created": "Triggered when a new conversation is created",
            "conversation.updated": "Triggered when a conversation is updated",
            "document.uploaded": "Triggered when a document is uploaded",
            "document.processed": "Triggered when a document is processed for RAG",
            "feedback.created": "Triggered when feedback is added to a message",
            "share.created": "Triggered when a conversation share link is created",
        },
    }


@router.post("/", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    data: WebhookCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """Create a new webhook."""
    webhook_service = WebhookService(db)

    try:
        webhook = await webhook_service.create_webhook(
            user_id=user_id,
            url=str(data.url),
            events=data.events,
            secret=data.secret,
        )

        return WebhookResponse(
            id=webhook.id,
            url=webhook.url,
            events=webhook.events,
            is_active=webhook.is_active,
            created_at=webhook.created_at.isoformat(),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[WebhookResponse]:
    """List user's webhooks."""
    webhook_service = WebhookService(db)

    webhooks = await webhook_service.list_webhooks(user_id)

    return [
        WebhookResponse(
            id=wh.id,
            url=wh.url,
            events=wh.events,
            is_active=wh.is_active,
            created_at=wh.created_at.isoformat(),
        )
        for wh in webhooks
    ]


@router.post("/{webhook_id}/toggle")
async def toggle_webhook(
    webhook_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Activate/deactivate a webhook."""
    webhook_service = WebhookService(db)

    webhook = await webhook_service.toggle_webhook(webhook_id, user_id)

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return {
        "id": webhook.id,
        "is_active": webhook.is_active,
    }


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook."""
    webhook_service = WebhookService(db)

    deleted = await webhook_service.delete_webhook(webhook_id, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
