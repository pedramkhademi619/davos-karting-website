from __future__ import annotations

from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limit_decision import RateLimitDecision
from davos.shared_kernel.application.rate_limiter import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    """Single-process limiter for tests and local development only.

    It does NOT work across API replicas; production wiring uses ``RedisRateLimiter``.
    """

    def __init__(self, clock: Clock) -> None:
        self._clock = clock
        # counter key -> (expires_at epoch seconds, hits in the current window)
        self._counters: dict[str, tuple[int, int]] = {}

    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
        now = int(self._clock.now().timestamp())
        window = now // window_seconds
        window_end = (window + 1) * window_seconds
        counter_key = f"{key}:{window_seconds}:{window}"

        self._counters = {k: v for k, v in self._counters.items() if v[0] > now}
        _, count = self._counters.get(counter_key, (window_end, 0))
        count += 1
        self._counters[counter_key] = (window_end, count)
        return RateLimitDecision(allowed=count <= limit, retry_after_seconds=window_end - now)
