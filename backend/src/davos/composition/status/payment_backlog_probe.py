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
    "SELECT status, count(*), min(updated_at) FROM payments_attempts"
    " WHERE status IN ('verifying', 'unknown', 'refund_pending') GROUP BY status"
)
_LABELS = {
    "verifying": "در حال تایید با بانک",
    "unknown": "نامشخص (منتظر پیگیری)",
    "refund_pending": "منتظر بازگشت وجه",
}


class PaymentBacklogProbe(ServiceProbe):
    key = "payment_backlog"
    group = "برنامه"
    label = "پرداخت‌های باز (نیازمند پیگیری)"

    def __init__(self, engine: AsyncEngine, clock: Clock) -> None:
        self._engine = engine
        self._clock = clock

    async def check(self) -> ProbeResult:
        async with self._engine.connect() as connection:
            rows = (await connection.execute(_QUERY)).all()
        now = self._clock.now()
        parts: list[ServicePart] = []
        level = StatusLevel.OK
        for status, count, oldest in rows:
            age = (now - oldest).total_seconds()
            stuck = age > 600
            if stuck:
                level = StatusLevel.DEGRADED
            parts.append(
                ServicePart(
                    _LABELS[status],
                    StatusLevel.DEGRADED if stuck else StatusLevel.OK,
                    f"{fa(count)} مورد، قدیمی‌ترین {duration(age)} پیش",
                )
            )
        if not rows:
            return ProbeResult(StatusLevel.OK, "هیچ پرداخت بلاتکلیفی نیست.")
        summary = (
            "پرداخت‌هایی بیش از ۱۰ دقیقه بلاتکلیف مانده‌اند؛ بخش «پرداخت‌ها» را ببینید."
            if level is StatusLevel.DEGRADED
            else "چند پرداخت در حال پیگیری خودکار است."
        )
        return ProbeResult(level, summary, tuple(parts))
