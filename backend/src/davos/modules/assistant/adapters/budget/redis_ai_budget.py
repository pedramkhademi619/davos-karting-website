from __future__ import annotations

from redis.asyncio import Redis

from davos.modules.assistant.application.ports.ai_budget_port import AiBudgetPort
from davos.shared_kernel.application.clock import Clock

_TWO_DAYS = 172_800


class RedisAiBudget(AiBudgetPort):
    """Daily token counter shared by every API replica.

    Reservation is INCRBY-then-check, so concurrent callers can never jointly exceed the limit:
    the caller that pushes the counter over rolls its own reservation back.
    """

    def __init__(self, redis: Redis, *, daily_limit: int, clock: Clock) -> None:
        self._redis = redis
        self._limit = daily_limit
        self._clock = clock

    def _key(self) -> str:
        return f"ai:budget:tokens:{self._clock.now().date().isoformat()}"

    async def try_reserve(self, tokens: int) -> bool:
        key = self._key()
        total = int(await self._redis.incrby(key, tokens))
        await self._redis.expire(key, _TWO_DAYS)
        if total > self._limit:
            await self._redis.decrby(key, tokens)
            return False
        return True

    async def settle(self, reserved: int, actual: int) -> None:
        delta = actual - reserved
        if delta:
            await self._redis.incrby(self._key(), delta)

    async def release(self, reserved: int) -> None:
        await self._redis.decrby(self._key(), reserved)
