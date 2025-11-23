"""Advanced search service for conversations and messages."""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.conversation import Conversation, Message
from app.models.analytics import Document
from app.core.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for advanced search and filtering."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize search service."""
        self.db = db

    async def search_conversations(
        self,
        user_id: str,
        query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model_provider: Optional[str] = None,
        has_documents: Optional[bool] = None,
        min_messages: Optional[int] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Advanced conversation search with filters."""
        # Base query
        query_stmt = select(Conversation).where(Conversation.user_id == user_id)

        # Text search in title
        if query:
            query_stmt = query_stmt.where(
                Conversation.title.ilike(f"%{query}%")
            )

        # Date filters
        if start_date:
            query_stmt = query_stmt.where(Conversation.created_at >= start_date)
        if end_date:
            query_stmt = query_stmt.where(Conversation.created_at <= end_date)

        # Model provider filter
        if model_provider:
            query_stmt = query_stmt.where(
                Conversation.model_config["provider"].astext == model_provider
            )

        # Message count filter
        if min_messages:
            # Subquery to count messages
            message_count = (
                select(func.count(Message.id))
                .where(Message.conversation_id == Conversation.id)
                .scalar_subquery()
            )
            query_stmt = query_stmt.where(message_count >= min_messages)

        # Sorting
        sort_field = getattr(Conversation, sort_by, Conversation.updated_at)
        if sort_order == "asc":
            query_stmt = query_stmt.order_by(sort_field.asc())
        else:
            query_stmt = query_stmt.order_by(sort_field.desc())

        # Pagination
        query_stmt = query_stmt.limit(limit).offset(offset)

        # Execute
        result = await self.db.execute(query_stmt)
        conversations = list(result.scalars().all())

        # Get total count
        count_stmt = select(func.count(Conversation.id)).where(
            Conversation.user_id == user_id
        )
        if query:
            count_stmt = count_stmt.where(Conversation.title.ilike(f"%{query}%"))
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        return {
            "results": conversations,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def search_messages(
        self,
        user_id: str,
        query: str,
        conversation_id: Optional[str] = None,
        role: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search within messages content."""
        # Base query with join to check user ownership
        query_stmt = (
            select(Message)
            .join(Conversation)
            .where(
                Conversation.user_id == user_id,
                Message.content.ilike(f"%{query}%")
            )
        )

        # Filter by conversation
        if conversation_id:
            query_stmt = query_stmt.where(Message.conversation_id == conversation_id)

        # Filter by role
        if role:
            query_stmt = query_stmt.where(Message.role == role)

        # Order by relevance (most recent first)
        query_stmt = query_stmt.order_by(Message.created_at.desc())

        # Pagination
        query_stmt = query_stmt.limit(limit).offset(offset)

        # Execute
        result = await self.db.execute(query_stmt)
        messages = list(result.scalars().all())

        # Get total count
        count_stmt = (
            select(func.count(Message.id))
            .join(Conversation)
            .where(
                Conversation.user_id == user_id,
                Message.content.ilike(f"%{query}%")
            )
        )
        if conversation_id:
            count_stmt = count_stmt.where(Message.conversation_id == conversation_id)
        if role:
            count_stmt = count_stmt.where(Message.role == role)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        return {
            "results": messages,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def search_documents(
        self,
        user_id: str,
        query: Optional[str] = None,
        file_type: Optional[str] = None,
        processed_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Search uploaded documents."""
        query_stmt = select(Document).where(Document.user_id == user_id)

        # Text search in filename
        if query:
            query_stmt = query_stmt.where(
                Document.original_filename.ilike(f"%{query}%")
            )

        # File type filter
        if file_type:
            query_stmt = query_stmt.where(Document.file_type == file_type)

        # Processed filter
        if processed_only:
            query_stmt = query_stmt.where(Document.processed == True)

        # Sorting
        sort_field = getattr(Document, sort_by, Document.created_at)
        if sort_order == "asc":
            query_stmt = query_stmt.order_by(sort_field.asc())
        else:
            query_stmt = query_stmt.order_by(sort_field.desc())

        # Pagination
        query_stmt = query_stmt.limit(limit).offset(offset)

        # Execute
        result = await self.db.execute(query_stmt)
        documents = list(result.scalars().all())

        # Get total count
        count_stmt = select(func.count(Document.id)).where(Document.user_id == user_id)
        if query:
            count_stmt = count_stmt.where(Document.original_filename.ilike(f"%{query}%"))
        if file_type:
            count_stmt = count_stmt.where(Document.file_type == file_type)

        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar()

        return {
            "results": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    async def get_search_suggestions(
        self,
        user_id: str,
        partial_query: str,
        limit: int = 5,
    ) -> List[str]:
        """Get search suggestions based on partial query."""
        # Get conversation titles that match
        result = await self.db.execute(
            select(Conversation.title)
            .where(
                Conversation.user_id == user_id,
                Conversation.title.ilike(f"%{partial_query}%")
            )
            .limit(limit)
        )

        suggestions = [row[0] for row in result.all()]
        return suggestions
