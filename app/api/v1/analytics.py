"""Analytics and feedback endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.services.analytics_service import AnalyticsService

router = APIRouter()


class FeedbackRequest(BaseModel):
    """Request schema for message feedback."""

    message_id: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_type: Optional[str] = Field(None, pattern="^(helpful|unhelpful|inappropriate)$")
    comment: Optional[str] = Field(None, max_length=500)


class UsageStatsResponse(BaseModel):
    """Response schema for usage statistics."""

    total_requests: int
    total_tokens: int
    total_cost: float
    average_latency_ms: float
    by_provider: dict
    by_model: dict


class FeedbackStatsResponse(BaseModel):
    """Response schema for feedback statistics."""

    total_feedback: int
    average_rating: float
    feedback_types: dict


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def add_feedback(
    request: FeedbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Add feedback for a message."""
    analytics_service = AnalyticsService(db)

    try:
        feedback = await analytics_service.add_message_feedback(
            message_id=request.message_id,
            user_id=user_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
        )
        return {"message": "Feedback added successfully", "id": feedback.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add feedback: {str(e)}")


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> UsageStatsResponse:
    """Get usage statistics for the current user."""
    analytics_service = AnalyticsService(db)

    stats = await analytics_service.get_user_stats(user_id, start_date, end_date)
    return UsageStatsResponse(**stats)


@router.get("/feedback/stats", response_model=FeedbackStatsResponse)
async def get_feedback_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> FeedbackStatsResponse:
    """Get feedback statistics (admin only for now)."""
    analytics_service = AnalyticsService(db)

    stats = await analytics_service.get_feedback_stats(start_date, end_date)
    return FeedbackStatsResponse(**stats)
