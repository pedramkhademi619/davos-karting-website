from __future__ import annotations

import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.status.persian_text import fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel

_SLOW_MS = 500


class DatabaseProbe(ServiceProbe):
    key = "database"
    group = "زیرساخت"
    label = "پایگاه داده (PostgreSQL)"

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def check(self) -> ProbeResult:
        started = time.monotonic()
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
            latency = int((time.monotonic() - started) * 1000)
            version = (await connection.execute(text("SELECT version_num FROM alembic_version"))).scalar_one_or_none()
            size = (await connection.execute(text("SELECT pg_database_size(current_database())"))).scalar_one()
            used, limit = (
                await connection.execute(
                    text(
                        "SELECT (SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()),"
                        " current_setting('max_connections')::int"
                    )
                )
            ).one()
        parts = (
            ServicePart("نسخه ساختار جدول‌ها", StatusLevel.OK, fa(version or "—")),
            ServicePart("حجم دیتابیس", StatusLevel.OK, f"{fa(round(size / 1_048_576, 1))} مگابایت"),
            ServicePart(
                "اتصال‌های باز",
                StatusLevel.DEGRADED if used > 0.8 * limit else StatusLevel.OK,
                f"{fa(used)} از {fa(limit)}",
            ),
        )
        level = StatusLevel.DEGRADED if latency > _SLOW_MS or used > 0.8 * limit else StatusLevel.OK
        summary = "کند است." if latency > _SLOW_MS else "در دسترس است."
        return ProbeResult(level, summary, parts, latency)
