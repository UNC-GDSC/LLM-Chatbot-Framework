"""Webhook service for event notifications."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String, DateTime, Boolean, JSON
from sqlalchemy.orm import declarative_base

from app.core.database import Base
from app.core.logging import get_logger
import uuid

logger = get_logger(__name__)


class Webhook(Base):
    """Webhook model for storing webhook configurations."""

    __tablename__ = "webhooks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    url = Column(String, nullable=False)
    events = Column(JSON, nullable=False)  # List of event types to listen for
    is_active = Column(Boolean, default=True)
    secret = Column(String, nullable=True)  # For signature verification
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookService:
    """Service for managing and triggering webhooks."""

    # Supported event types
    SUPPORTED_EVENTS = [
        "message.created",
        "conversation.created",
        "conversation.updated",
        "document.uploaded",
        "document.processed",
        "feedback.created",
        "share.created",
    ]

    def __init__(self, db: AsyncSession) -> None:
        """Initialize webhook service."""
        self.db = db

    async def trigger_webhook(
        self,
        user_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> None:
        """Trigger webhooks for a specific event."""
        if event_type not in self.SUPPORTED_EVENTS:
            logger.warning(f"Unsupported event type: {event_type}")
            return

        # Get active webhooks for this user and event type
        from sqlalchemy import select
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active == True,
            )
        )
        webhooks = result.scalars().all()

        # Filter webhooks that subscribe to this event
        for webhook in webhooks:
            if event_type in webhook.events:
                await self._send_webhook(webhook, event_type, payload)

    async def _send_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any],
    ) -> bool:
        """Send webhook HTTP request."""
        try:
            webhook_payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": payload,
            }

            headers = {
                "Content-Type": "application/json",
                "User-Agent": "LLM-Chatbot-Framework-Webhook/1.0",
            }

            # Add signature if secret is configured
            if webhook.secret:
                import hmac
                import hashlib
                signature = hmac.new(
                    webhook.secret.encode(),
                    json.dumps(webhook_payload).encode(),
                    hashlib.sha256,
                ).hexdigest()
                headers["X-Webhook-Signature"] = signature

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    webhook.url,
                    json=webhook_payload,
                    headers=headers,
                )

                if response.status_code in [200, 201, 204]:
                    logger.info(f"Webhook sent successfully to {webhook.url}")
                    return True
                else:
                    logger.warning(f"Webhook failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False

    async def create_webhook(
        self,
        user_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
    ) -> Webhook:
        """Create a new webhook."""
        # Validate events
        invalid_events = [e for e in events if e not in self.SUPPORTED_EVENTS]
        if invalid_events:
            raise ValueError(f"Invalid events: {invalid_events}")

        webhook = Webhook(
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
        )

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info(f"Created webhook for user {user_id}")
        return webhook

    async def list_webhooks(self, user_id: str) -> List[Webhook]:
        """List user's webhooks."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(Webhook).where(Webhook.user_id == user_id)
        )
        return list(result.scalars().all())

    async def delete_webhook(self, webhook_id: str, user_id: str) -> bool:
        """Delete a webhook."""
        from sqlalchemy import select, delete as sql_delete
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            )
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            return False

        await self.db.execute(
            sql_delete(Webhook).where(Webhook.id == webhook_id)
        )
        await self.db.commit()

        logger.info(f"Deleted webhook {webhook_id}")
        return True

    async def toggle_webhook(self, webhook_id: str, user_id: str) -> Optional[Webhook]:
        """Activate/deactivate a webhook."""
        from sqlalchemy import select
        result = await self.db.execute(
            select(Webhook).where(
                Webhook.id == webhook_id,
                Webhook.user_id == user_id,
            )
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            return None

        webhook.is_active = not webhook.is_active
        await self.db.commit()
        await self.db.refresh(webhook)

        return webhook
