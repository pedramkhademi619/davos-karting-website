from __future__ import annotations

from abc import ABC, abstractmethod

from davos.shared_kernel.application.rate_limit_decision import RateLimitDecision


class RateLimiter(ABC):
    """Fixed-window limiter backed by shared state so it works across API replicas."""

    @abstractmethod
    async def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision: ...
