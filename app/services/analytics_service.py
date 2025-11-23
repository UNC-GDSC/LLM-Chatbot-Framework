"""Analytics and usage tracking service."""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.analytics import UsageStats, MessageFeedback
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics and usage tracking."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize analytics service."""
        self.db = db

    async def track_usage(
        self,
        user_id: str,
        conversation_id: Optional[str],
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        latency_ms: Optional[int] = None,
    ) -> UsageStats:
        """Track API usage."""
        total_tokens = prompt_tokens + completion_tokens

        # Calculate estimated cost (simplified)
        cost = self._estimate_cost(provider, model, prompt_tokens, completion_tokens)

        usage = UsageStats(
            user_id=user_id,
            conversation_id=conversation_id,
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost=cost,
            latency_ms=latency_ms,
        )

        self.db.add(usage)
        await self.db.commit()
        await self.db.refresh(usage)

        return usage

    def _estimate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Estimate cost based on provider and model (simplified pricing)."""
        # Simplified pricing - should be updated with actual pricing
        pricing = {
            "openai": {
                "gpt-4": {"prompt": 0.03 / 1000, "completion": 0.06 / 1000},
                "gpt-3.5-turbo": {"prompt": 0.001 / 1000, "completion": 0.002 / 1000},
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"prompt": 0.003 / 1000, "completion": 0.015 / 1000},
                "claude-3-opus-20240229": {"prompt": 0.015 / 1000, "completion": 0.075 / 1000},
            },
        }

        provider_pricing = pricing.get(provider, {})
        model_pricing = provider_pricing.get(model, {"prompt": 0, "completion": 0})

        cost = (
            prompt_tokens * model_pricing["prompt"]
            + completion_tokens * model_pricing["completion"]
        )

        return round(cost, 6)

    async def get_user_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics for a user."""
        query = select(UsageStats).where(UsageStats.user_id == user_id)

        if start_date:
            query = query.where(UsageStats.created_at >= start_date)
        if end_date:
            query = query.where(UsageStats.created_at <= end_date)

        result = await self.db.execute(query)
        stats = list(result.scalars().all())

        if not stats:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "average_latency_ms": 0,
                "by_provider": {},
                "by_model": {},
            }

        total_requests = len(stats)
        total_tokens = sum(s.total_tokens for s in stats)
        total_cost = sum(s.cost or 0 for s in stats)
        avg_latency = sum(s.latency_ms or 0 for s in stats) / total_requests

        # Group by provider
        by_provider = {}
        for stat in stats:
            if stat.provider not in by_provider:
                by_provider[stat.provider] = {"requests": 0, "tokens": 0, "cost": 0.0}
            by_provider[stat.provider]["requests"] += 1
            by_provider[stat.provider]["tokens"] += stat.total_tokens
            by_provider[stat.provider]["cost"] += stat.cost or 0

        # Group by model
        by_model = {}
        for stat in stats:
            if stat.model not in by_model:
                by_model[stat.model] = {"requests": 0, "tokens": 0, "cost": 0.0}
            by_model[stat.model]["requests"] += 1
            by_model[stat.model]["tokens"] += stat.total_tokens
            by_model[stat.model]["cost"] += stat.cost or 0

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_cost": round(total_cost, 4),
            "average_latency_ms": round(avg_latency, 2),
            "by_provider": by_provider,
            "by_model": by_model,
        }

    async def add_message_feedback(
        self,
        message_id: str,
        user_id: str,
        rating: Optional[int] = None,
        feedback_type: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> MessageFeedback:
        """Add feedback for a message."""
        feedback = MessageFeedback(
            message_id=message_id,
            user_id=user_id,
            rating=rating,
            feedback_type=feedback_type,
            comment=comment,
        )

        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)

        logger.info(f"Added feedback for message {message_id}")
        return feedback

    async def get_feedback_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get feedback statistics."""
        query = select(MessageFeedback)

        if start_date:
            query = query.where(MessageFeedback.created_at >= start_date)
        if end_date:
            query = query.where(MessageFeedback.created_at <= end_date)

        result = await self.db.execute(query)
        feedbacks = list(result.scalars().all())

        if not feedbacks:
            return {
                "total_feedback": 0,
                "average_rating": 0.0,
                "feedback_types": {},
            }

        ratings = [f.rating for f in feedbacks if f.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

        feedback_types = {}
        for f in feedbacks:
            if f.feedback_type:
                feedback_types[f.feedback_type] = feedback_types.get(f.feedback_type, 0) + 1

        return {
            "total_feedback": len(feedbacks),
            "average_rating": round(avg_rating, 2),
            "feedback_types": feedback_types,
        }
