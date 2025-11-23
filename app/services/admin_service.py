"""Admin service for system management and user administration."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, delete

from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.analytics import UsageStats, MessageFeedback, Document
from app.core.logging import get_logger

logger = get_logger(__name__)


class AdminService:
    """Service for admin operations and system management."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize admin service."""
        self.db = db

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        # User stats
        user_count_result = await self.db.execute(select(func.count(User.id)))
        total_users = user_count_result.scalar()

        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar()

        # Conversation stats
        conv_count_result = await self.db.execute(select(func.count(Conversation.id)))
        total_conversations = conv_count_result.scalar()

        msg_count_result = await self.db.execute(select(func.count(Message.id)))
        total_messages = msg_count_result.scalar()

        # Document stats
        doc_count_result = await self.db.execute(select(func.count(Document.id)))
        total_documents = doc_count_result.scalar()

        # Usage stats (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        usage_result = await self.db.execute(
            select(
                func.sum(UsageStats.total_tokens),
                func.sum(UsageStats.cost),
                func.count(UsageStats.id)
            ).where(UsageStats.created_at >= thirty_days_ago)
        )
        usage_row = usage_result.one()

        # Feedback stats
        feedback_result = await self.db.execute(
            select(
                func.avg(MessageFeedback.rating),
                func.count(MessageFeedback.id)
            ).where(MessageFeedback.rating.isnot(None))
        )
        feedback_row = feedback_result.one()

        return {
            "users": {
                "total": total_users,
                "active": active_users,
            },
            "content": {
                "conversations": total_conversations,
                "messages": total_messages,
                "documents": total_documents,
            },
            "usage_last_30_days": {
                "total_tokens": int(usage_row[0] or 0),
                "total_cost": float(usage_row[1] or 0),
                "requests": int(usage_row[2] or 0),
            },
            "feedback": {
                "average_rating": round(float(feedback_row[0] or 0), 2),
                "total_ratings": int(feedback_row[1] or 0),
            },
        }

    async def list_users(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = False,
    ) -> List[User]:
        """List all users (admin only)."""
        query = select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)

        if active_only:
            query = query.where(User.is_active == True)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_details(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed user information."""
        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        # Get user stats
        conv_count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        conversation_count = conv_count_result.scalar()

        msg_count_result = await self.db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(Conversation.user_id == user_id)
        )
        message_count = msg_count_result.scalar()

        doc_count_result = await self.db.execute(
            select(func.count(Document.id)).where(Document.user_id == user_id)
        )
        document_count = doc_count_result.scalar()

        usage_result = await self.db.execute(
            select(
                func.sum(UsageStats.total_tokens),
                func.sum(UsageStats.cost)
            ).where(UsageStats.user_id == user_id)
        )
        usage_row = usage_result.one()

        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "created_at": user.created_at,
            },
            "stats": {
                "conversations": conversation_count,
                "messages": message_count,
                "documents": document_count,
                "total_tokens": int(usage_row[0] or 0),
                "total_cost": float(usage_row[1] or 0),
            },
        }

    async def toggle_user_status(self, user_id: str) -> Optional[User]:
        """Activate or deactivate a user."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        user.is_active = not user.is_active
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User {user_id} status changed to: {user.is_active}")
        return user

    async def delete_user_data(self, user_id: str) -> bool:
        """Delete all user data (conversations, documents, etc.)."""
        try:
            # Delete conversations (cascade will delete messages)
            await self.db.execute(
                delete(Conversation).where(Conversation.user_id == user_id)
            )

            # Delete documents
            await self.db.execute(
                delete(Document).where(Document.user_id == user_id)
            )

            # Delete usage stats
            await self.db.execute(
                delete(UsageStats).where(UsageStats.user_id == user_id)
            )

            await self.db.commit()
            logger.info(f"Deleted all data for user: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting user data: {e}")
            await self.db.rollback()
            return False

    async def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get recent system activity."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        # Recent conversations
        conv_result = await self.db.execute(
            select(Conversation)
            .where(Conversation.created_at >= cutoff_time)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        recent_conversations = [
            {
                "id": conv.id,
                "user_id": conv.user_id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat(),
            }
            for conv in conv_result.scalars().all()
        ]

        # Recent documents
        doc_result = await self.db.execute(
            select(Document)
            .where(Document.created_at >= cutoff_time)
            .order_by(Document.created_at.desc())
            .limit(limit)
        )
        recent_documents = [
            {
                "id": doc.id,
                "user_id": doc.user_id,
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "created_at": doc.created_at.isoformat(),
            }
            for doc in doc_result.scalars().all()
        ]

        # Recent feedback
        feedback_result = await self.db.execute(
            select(MessageFeedback)
            .where(MessageFeedback.created_at >= cutoff_time)
            .order_by(MessageFeedback.created_at.desc())
            .limit(limit)
        )
        recent_feedback = [
            {
                "id": fb.id,
                "message_id": fb.message_id,
                "rating": fb.rating,
                "feedback_type": fb.feedback_type,
                "created_at": fb.created_at.isoformat(),
            }
            for fb in feedback_result.scalars().all()
        ]

        return {
            "conversations": recent_conversations,
            "documents": recent_documents,
            "feedback": recent_feedback,
        }

    async def cleanup_old_data(self, days: int = 90) -> Dict[str, int]:
        """Clean up old data (conversations, documents, etc.)."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old conversations
        conv_result = await self.db.execute(
            delete(Conversation).where(Conversation.updated_at < cutoff_date)
        )
        deleted_conversations = conv_result.rowcount

        # Delete old usage stats
        stats_result = await self.db.execute(
            delete(UsageStats).where(UsageStats.created_at < cutoff_date)
        )
        deleted_stats = stats_result.rowcount

        await self.db.commit()

        logger.info(f"Cleaned up {deleted_conversations} conversations and {deleted_stats} usage stats")

        return {
            "conversations": deleted_conversations,
            "usage_stats": deleted_stats,
        }
