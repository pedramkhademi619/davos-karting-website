from __future__ import annotations

from redis.asyncio import Redis

_KEY = "davos:task-heartbeats"


class TaskHeartbeat:
    """The last time each scheduled job finished, kept in Redis so the admin panel can tell a stopped worker or
    scheduler from a quiet one."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def beat(self, task: str, at_epoch: float) -> None:
        await self._redis.hset(_KEY, task, str(at_epoch))

    async def last_runs(self) -> dict[str, float]:
        raw = await self._redis.hgetall(_KEY)
        out: dict[str, float] = {}
        for name, value in raw.items():
            try:
                out[name.decode() if isinstance(name, bytes) else str(name)] = float(value)
            except ValueError:
                continue
        return out
