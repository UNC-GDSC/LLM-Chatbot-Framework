"""Redis cache manager."""

from typing import Optional, Any
import json
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheManager:
    """Redis cache manager for caching responses and data."""

    def __init__(self) -> None:
        """Initialize cache manager."""
        self.redis_client: Optional[redis.Redis] = None
        self.enabled = bool(settings.REDIS_URL)

    async def connect(self) -> None:
        """Connect to Redis."""
        if not self.enabled:
            logger.info("Redis not configured, caching disabled")
            return

        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.enabled or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error: {e}")
        return None

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.enabled or not self.redis_client:
            return False

        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            await self.redis_client.setex(
                key, ttl, json.dumps(value)
            )
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if not self.enabled or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.enabled or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
        return 0


# Global cache instance
cache = CacheManager()
