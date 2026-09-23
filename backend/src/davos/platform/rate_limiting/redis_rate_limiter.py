from __future__ import annotations

from redis.asyncio import Redis

from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limit_decision import RateLimitDecision
from davos.shared_kernel.application.rate_limiter import RateLimiter


class RedisRateLimiter(RateLimiter):
    """Fixed-window counter in Redis: consistent across every API replica."""

    def __init__(self, redis: Redis, clock: Clock) -> None:
        self._redis = redis
        self._clock = clock

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        now = int(self._clock.now().timestamp())
        window = now // window_seconds
        redis_key = f"rl:{key}:{window_seconds}:{window}"
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_seconds)
            count, _ = await pipe.execute()
        retry_after = window_seconds - (now % window_seconds)
        return RateLimitDecision(allowed=int(count) <= limit, retry_after_seconds=retry_after)
