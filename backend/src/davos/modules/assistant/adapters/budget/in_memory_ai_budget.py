from __future__ import annotations

from davos.modules.assistant.application.ports.ai_budget_port import AiBudgetPort
from davos.shared_kernel.application.clock import Clock


class InMemoryAiBudget(AiBudgetPort):
    """Single-process budget for tests and local development; production uses RedisAiBudget."""

    def __init__(self, *, daily_limit: int, clock: Clock) -> None:
        self._limit = daily_limit
        self._clock = clock
        self._used: dict[str, int] = {}

    def _day(self) -> str:
        return self._clock.now().date().isoformat()

    @property
    def used_today(self) -> int:
        return self._used.get(self._day(), 0)

    async def try_reserve(self, tokens: int) -> bool:
        day = self._day()
        if self._used.get(day, 0) + tokens > self._limit:
            return False
        self._used[day] = self._used.get(day, 0) + tokens
        return True

    async def settle(self, reserved: int, actual: int) -> None:
        day = self._day()
        self._used[day] = max(self._used.get(day, 0) + actual - reserved, 0)

    async def release(self, reserved: int) -> None:
        day = self._day()
        self._used[day] = max(self._used.get(day, 0) - reserved, 0)
