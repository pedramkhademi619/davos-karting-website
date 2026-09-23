import pytest
from redis.asyncio import Redis

from davos.platform.rate_limiting.redis_rate_limiter import RedisRateLimiter
from tests.fakes.fixed_clock import FixedClock

pytestmark = pytest.mark.integration


async def test_counters_are_shared_between_replicas(redis_client: Redis, clock: FixedClock) -> None:
    replica_a = RedisRateLimiter(redis_client, clock)
    replica_b = RedisRateLimiter(redis_client, clock)

    assert (await replica_a.hit("k", limit=2, window_seconds=60)).allowed
    assert (await replica_b.hit("k", limit=2, window_seconds=60)).allowed
    blocked = await replica_a.hit("k", limit=2, window_seconds=60)
    assert not blocked.allowed
    assert 0 < blocked.retry_after_seconds <= 60


async def test_window_rolls_over(redis_client: Redis, clock: FixedClock) -> None:
    limiter = RedisRateLimiter(redis_client, clock)
    assert (await limiter.hit("k", limit=1, window_seconds=60)).allowed
    assert not (await limiter.hit("k", limit=1, window_seconds=60)).allowed
    clock.advance(seconds=60)
    assert (await limiter.hit("k", limit=1, window_seconds=60)).allowed


async def test_keys_are_isolated(redis_client: Redis, clock: FixedClock) -> None:
    limiter = RedisRateLimiter(redis_client, clock)
    assert (await limiter.hit("a", limit=1, window_seconds=60)).allowed
    assert (await limiter.hit("b", limit=1, window_seconds=60)).allowed
