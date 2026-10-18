from __future__ import annotations

import time

from redis.asyncio import Redis

from davos.composition.status.persian_text import duration, fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel

_SLOW_MS = 200


class RedisProbe(ServiceProbe):
    key = "redis"
    group = "زیرساخت"
    label = "کش و صف (Redis)"

    def __init__(self, redis: Redis | None) -> None:
        self._redis = redis

    async def check(self) -> ProbeResult:
        if self._redis is None:
            return ProbeResult(StatusLevel.DISABLED, "Redis در این محیط وصل نیست (محدودکننده درخواست در حافظه است).")
        started = time.monotonic()
        await self._redis.ping()
        latency = int((time.monotonic() - started) * 1000)
        info = await self._redis.info()
        used = int(info.get("used_memory", 0))
        peak_limit = int(info.get("maxmemory", 0))
        parts = [
            ServicePart("حافظه مصرفی", StatusLevel.OK, f"{fa(round(used / 1_048_576, 1))} مگابایت"),
            ServicePart("کلاینت‌های وصل", StatusLevel.OK, fa(info.get("connected_clients", 0))),
            ServicePart("روشن بودن", StatusLevel.OK, duration(float(info.get("uptime_in_seconds", 0)))),
        ]
        level = StatusLevel.OK
        if peak_limit and used > 0.85 * peak_limit:
            level = StatusLevel.DEGRADED
            parts.append(ServicePart("سقف حافظه", StatusLevel.DEGRADED, "نزدیک پر شدن است"))
        if latency > _SLOW_MS:
            level = StatusLevel.DEGRADED
        return ProbeResult(level, "کند است." if latency > _SLOW_MS else "در دسترس است.", tuple(parts), latency)
