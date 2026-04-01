"""
Redis client for caching, streak tracking, and session storage.
"""

import json
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()

# ── Redis Connection Pool ────────────────────────────────────
redis_pool = aioredis.ConnectionPool.from_url(
    settings.redis_url,
    max_connections=50,
    decode_responses=True,
)

redis_client = aioredis.Redis(connection_pool=redis_pool)


class RedisService:
    """High-level Redis operations for the application."""

    def __init__(self, client: aioredis.Redis = redis_client):
        self.client = client

    # ── Generic Cache ────────────────────────────────────────
    async def set_cache(
        self, key: str, value: Any, ttl: int = settings.redis_cache_ttl
    ) -> None:
        """Store a JSON-serializable value with TTL."""
        await self.client.setex(key, ttl, json.dumps(value))

    async def get_cache(self, key: str) -> Optional[Any]:
        """Retrieve and deserialize a cached value."""
        data = await self.client.get(key)
        return json.loads(data) if data else None

    async def delete_cache(self, key: str) -> None:
        await self.client.delete(key)

    # ── Streak Operations ────────────────────────────────────
    async def get_streak(self, user_id: str) -> dict:
        """Get current streak data for a user."""
        key = f"streak:{user_id}"
        data = await self.client.hgetall(key)
        if not data:
            return {"current": 0, "longest": 0, "last_date": None}
        return {
            "current": int(data.get("current", 0)),
            "longest": int(data.get("longest", 0)),
            "last_date": data.get("last_date"),
        }

    async def update_streak(self, user_id: str, date_str: str) -> dict:
        """
        Update streak for a user on a given date.
        Increments if consecutive, resets if gap detected.
        """
        from datetime import date, datetime

        key = f"streak:{user_id}"
        current_data = await self.get_streak(user_id)

        today = datetime.strptime(date_str, "%Y-%m-%d").date()
        last_date = (
            datetime.strptime(current_data["last_date"], "%Y-%m-%d").date()
            if current_data["last_date"]
            else None
        )

        if last_date == today:
            # Already recorded today
            return current_data

        if last_date and (today - last_date).days == 1:
            # Consecutive day — increment
            new_current = current_data["current"] + 1
        elif last_date and (today - last_date).days > 1:
            # Gap detected — reset
            new_current = 1
        else:
            # First entry
            new_current = 1

        new_longest = max(new_current, current_data["longest"])

        await self.client.hset(key, mapping={
            "current": str(new_current),
            "longest": str(new_longest),
            "last_date": date_str,
        })

        return {
            "current": new_current,
            "longest": new_longest,
            "last_date": date_str,
        }

    async def reset_streak(self, user_id: str) -> None:
        """Reset a user's streak to zero."""
        key = f"streak:{user_id}"
        await self.client.delete(key)

    # ── Daily Plan Cache ─────────────────────────────────────
    async def cache_daily_plan(
        self, user_id: str, date_str: str, plan: dict
    ) -> None:
        """Cache a user's daily plan with 24-hour TTL."""
        key = f"daily_plan:{user_id}:{date_str}"
        await self.set_cache(key, plan, ttl=86400)

    async def get_cached_daily_plan(
        self, user_id: str, date_str: str
    ) -> Optional[dict]:
        key = f"daily_plan:{user_id}:{date_str}"
        return await self.get_cache(key)

    # ── Session ──────────────────────────────────────────────
    async def store_session(
        self, session_id: str, data: dict, ttl: int = 86400
    ) -> None:
        key = f"session:{session_id}"
        await self.set_cache(key, data, ttl=ttl)

    async def get_session(self, session_id: str) -> Optional[dict]:
        key = f"session:{session_id}"
        return await self.get_cache(key)


def get_redis_service() -> RedisService:
    """FastAPI dependency for Redis service."""
    return RedisService()
