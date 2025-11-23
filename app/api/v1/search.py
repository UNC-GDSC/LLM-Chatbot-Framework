"""Advanced search API endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.search_service import SearchService

router = APIRouter()


@router.get("/conversations")
async def search_conversations(
    query: Optional[str] = Query(None, min_length=1, max_length=200),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    model_provider: Optional[str] = None,
    min_messages: Optional[int] = Query(None, ge=1),
    sort_by: str = Query("updated_at", pattern="^(created_at|updated_at|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Advanced conversation search with filters."""
    search_service = SearchService(db)

    results = await search_service.search_conversations(
        user_id=user_id,
        query=query,
        start_date=start_date,
        end_date=end_date,
        model_provider=model_provider,
        min_messages=min_messages,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/messages")
async def search_messages(
    query: str = Query(..., min_length=1, max_length=200),
    conversation_id: Optional[str] = None,
    role: Optional[str] = Query(None, pattern="^(user|assistant)$"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Search within message content."""
    search_service = SearchService(db)

    results = await search_service.search_messages(
        user_id=user_id,
        query=query,
        conversation_id=conversation_id,
        role=role,
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/documents")
async def search_documents(
    query: Optional[str] = Query(None, min_length=1, max_length=200),
    file_type: Optional[str] = None,
    processed_only: bool = False,
    sort_by: str = Query("created_at", pattern="^(created_at|original_filename|file_size)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Search uploaded documents."""
    search_service = SearchService(db)

    results = await search_service.search_documents(
        user_id=user_id,
        query=query,
        file_type=file_type,
        processed_only=processed_only,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset,
    )

    return results


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=50),
    limit: int = Query(5, le=10),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get search suggestions based on partial query."""
    search_service = SearchService(db)

    suggestions = await search_service.get_search_suggestions(
        user_id=user_id,
        partial_query=q,
        limit=limit,
    )

    return {"suggestions": suggestions}
