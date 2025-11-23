"""Conversation sharing service."""

from typing import Optional
from datetime import datetime, timedelta
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.analytics import SharedConversation
from app.models.conversation import Conversation
from app.core.logging import get_logger

logger = get_logger(__name__)


class SharingService:
    """Service for sharing conversations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize sharing service."""
        self.db = db

    async def create_share_link(
        self,
        conversation_id: str,
        user_id: str,
        expires_in_days: Optional[int] = None,
    ) -> SharedConversation:
        """Create a shareable link for a conversation."""
        # Generate unique share token
        share_token = secrets.token_urlsafe(32)

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        # Create share record
        shared = SharedConversation(
            conversation_id=conversation_id,
            share_token=share_token,
            created_by=user_id,
            expires_at=expires_at,
        )

        self.db.add(shared)
        await self.db.commit()
        await self.db.refresh(shared)

        logger.info(f"Created share link for conversation {conversation_id}")
        return shared

    async def get_shared_conversation(
        self, share_token: str
    ) -> Optional[Conversation]:
        """Get conversation by share token."""
        # Get share record
        result = await self.db.execute(
            select(SharedConversation).where(
                SharedConversation.share_token == share_token,
                SharedConversation.is_active == True,
            )
        )
        shared = result.scalar_one_or_none()

        if not shared:
            return None

        # Check expiration
        if shared.expires_at and shared.expires_at < datetime.utcnow():
            return None

        # Increment view count
        shared.view_count += 1
        await self.db.commit()

        # Get conversation
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == shared.conversation_id)
        )
        return result.scalar_one_or_none()

    async def revoke_share_link(self, share_token: str, user_id: str) -> bool:
        """Revoke a share link."""
        result = await self.db.execute(
            select(SharedConversation).where(
                SharedConversation.share_token == share_token,
                SharedConversation.created_by == user_id,
            )
        )
        shared = result.scalar_one_or_none()

        if not shared:
            return False

        shared.is_active = False
        await self.db.commit()

        logger.info(f"Revoked share link {share_token}")
        return True

    async def get_conversation_shares(
        self, conversation_id: str, user_id: str
    ) -> list[SharedConversation]:
        """Get all share links for a conversation."""
        result = await self.db.execute(
            select(SharedConversation).where(
                SharedConversation.conversation_id == conversation_id,
                SharedConversation.created_by == user_id,
            )
        )
        return list(result.scalars().all())
