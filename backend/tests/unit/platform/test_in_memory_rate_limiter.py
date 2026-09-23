from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from tests.fakes.fixed_clock import FixedClock


async def test_blocks_after_the_limit_and_reports_time_until_reset() -> None:
    limiter = InMemoryRateLimiter(FixedClock())
    assert (await limiter.hit("k", limit=2, window_seconds=60)).allowed
    assert (await limiter.hit("k", limit=2, window_seconds=60)).allowed
    blocked = await limiter.hit("k", limit=2, window_seconds=60)
    assert not blocked.allowed and 0 < blocked.retry_after_seconds <= 60


async def test_counters_reset_when_the_window_rolls_over() -> None:
    clock = FixedClock()
    limiter = InMemoryRateLimiter(clock)
    await limiter.hit("k", limit=1, window_seconds=60)
    assert not (await limiter.hit("k", limit=1, window_seconds=60)).allowed
    clock.advance(seconds=60)
    assert (await limiter.hit("k", limit=1, window_seconds=60)).allowed


async def test_hits_with_a_short_window_do_not_erase_counters_of_a_longer_window() -> None:
    """Regression: pruning used window indexes, so a 1h hit wiped a 24h counter."""
    limiter = InMemoryRateLimiter(FixedClock())
    await limiter.hit("conversation", limit=2, window_seconds=86400)
    await limiter.hit("conversation", limit=2, window_seconds=86400)
    await limiter.hit("ip", limit=100, window_seconds=3600)  # different key, shorter window
    assert not (await limiter.hit("conversation", limit=2, window_seconds=86400)).allowed


async def test_different_keys_are_independent() -> None:
    limiter = InMemoryRateLimiter(FixedClock())
    assert (await limiter.hit("a", limit=1, window_seconds=60)).allowed
    assert (await limiter.hit("b", limit=1, window_seconds=60)).allowed
