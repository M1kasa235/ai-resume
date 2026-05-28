"""Rate limiting — Redis sliding-window with in-memory fallback."""
import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class SimpleRateLimiter:
    """In-memory fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self.requests: dict[str, list[float]] = {}
        self.default_limit = 200
        self.window = 60

    def is_allowed(self, key: str, limit: int | None = None) -> bool:
        if limit is None:
            limit = self.default_limit
        now = time.time()
        bucket = self.requests.get(key, [])
        bucket = [t for t in bucket if now - t < self.window]
        self.requests[key] = bucket
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


class RedisRateLimiter:
    """Redis sorted-set sliding-window rate limiter."""

    def __init__(self, default_limit: int = 200, window: int = 60) -> None:
        self.default_limit = default_limit
        self.window = window

    async def is_allowed(self, key: str, limit: int | None = None) -> bool:
        from app.core.redis import get_redis

        r = get_redis()
        if r is None:
            return _simple.is_allowed(key, limit)

        if limit is None:
            limit = self.default_limit

        now = time.time()
        window_start = now - self.window
        rkey = f"rl:{key}"

        try:
            async with r.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(rkey, 0, window_start)
                pipe.zcard(rkey)
                pipe.zadd(rkey, {str(now): now})
                pipe.expire(rkey, self.window + 10)
                _, count, _, _ = await pipe.execute()
            return count < limit
        except Exception:
            return _simple.is_allowed(key, limit)


_simple = SimpleRateLimiter()
_redis_rl = RedisRateLimiter()


async def _is_allowed(key: str, limit: int | None = None) -> bool:
    if settings.REDIS_RATE_LIMIT_ENABLED:
        return await _redis_rl.is_allowed(key, limit)
    return _simple.is_allowed(key, limit)


async def check_memory_llm_quota(user_id: int) -> None:
    from fastapi import HTTPException

    allowed = await _is_allowed(
        f"memory_llm:user:{user_id}", settings.MEMORY_LLM_RATE_LIMIT_PER_MINUTE
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="记忆处理请求过于频繁，请稍后再试")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        limit = 200
        if "/auth/login" in path or "/auth/register" in path:
            limit = 5

        allowed = await _is_allowed(client_ip, limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"error_code": "RATE_LIMIT_EXCEEDED", "detail": "请求过于频繁，请稍后再试"},
            )

        return await call_next(request)
