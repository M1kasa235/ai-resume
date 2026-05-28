"""Redis connection pool singleton (async)."""

import logging
from typing import Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

_pool: Optional[Redis] = None


async def init_redis(url: str) -> None:
    """Initialize Redis connection pool (call once at startup)."""
    global _pool
    if _pool is not None:
        return
    try:
        _pool = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=2)
        await _pool.ping()
        logger.info("Redis connected: %s", url)
    except Exception:
        logger.warning("Redis unavailable at %s — falling back to in-memory", url)
        _pool = None


async def close_redis() -> None:
    """Close Redis connection pool (call at shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Redis disconnected")


def get_redis() -> Optional[Redis]:
    """Get the Redis client, or None if unavailable."""
    return _pool
