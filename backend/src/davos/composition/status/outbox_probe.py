from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.status.persian_text import duration, fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.shared_kernel.application.clock import Clock

_QUERY = text(
    "SELECT count(*) FILTER (WHERE published_at IS NULL AND dead_lettered_at IS NULL),"
    " min(created_at) FILTER (WHERE published_at IS NULL AND dead_lettered_at IS NULL),"
    " count(*) FILTER (WHERE dead_lettered_at IS NOT NULL) FROM outbox_messages"
)


class OutboxProbe(ServiceProbe):
    key = "outbox"
    group = "برنامه"
    label = "صف رویدادها (پیامک، تایید رزرو، امتیاز)"

    def __init__(self, engine: AsyncEngine, clock: Clock) -> None:
        self._engine = engine
        self._clock = clock

    async def check(self) -> ProbeResult:
        async with self._engine.connect() as connection:
            pending, oldest, dead = (await connection.execute(_QUERY)).one()
        age = (self._clock.now() - oldest).total_seconds() if oldest else 0.0
        level = StatusLevel.OK
        if pending and age > 60:
            level = StatusLevel.DEGRADED
        if pending and age > 600:
            level = StatusLevel.DOWN
        if dead and level is StatusLevel.OK:
            level = StatusLevel.DEGRADED
        parts = (
            ServicePart("در انتظار ارسال", StatusLevel.OK if age <= 60 else level, fa(pending)),
            ServicePart("قدیمی‌ترین در صف", StatusLevel.OK if age <= 60 else level, duration(age) if pending else "—"),
            ServicePart("شکست‌خورده (نیاز به بررسی)", StatusLevel.DEGRADED if dead else StatusLevel.OK, fa(dead)),
        )
        summary = {
            StatusLevel.OK: "صف خالی یا در حال پردازش است.",
            StatusLevel.DEGRADED: "در صف تاخیر یا رویداد شکست‌خورده هست.",
            StatusLevel.DOWN: "رویدادها بیش از ۱۰ دقیقه است که ارسال نمی‌شوند.",
        }[level]
        return ProbeResult(level, summary, parts)
