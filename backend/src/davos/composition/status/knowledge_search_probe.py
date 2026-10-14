from __future__ import annotations

import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.status.persian_text import fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.platform.settings.app_settings import AppSettings


class KnowledgeSearchProbe(ServiceProbe):
    key = "knowledge_search"
    group = "برنامه"
    label = "جست‌وجوی دانش دستیار"

    def __init__(self, engine: AsyncEngine, settings: AppSettings) -> None:
        self._engine = engine
        self._settings = settings

    async def check(self) -> ProbeResult:
        async with self._engine.connect() as connection:
            extensions = {
                row[0]
                for row in await connection.execute(
                    text("SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pg_trgm')")
                )
            }
            entries = (await connection.execute(text("SELECT count(*) FROM assistant_knowledge_entries"))).scalar_one()
        parts = [
            ServicePart(
                "جست‌وجوی فارسی (pg_trgm)",
                StatusLevel.OK if "pg_trgm" in extensions else StatusLevel.DOWN,
                "فعال" if "pg_trgm" in extensions else "نصب نیست",
            ),
            ServicePart(
                "جست‌وجوی معنایی (pgvector)",
                StatusLevel.OK if "vector" in extensions else StatusLevel.DEGRADED,
                "فعال" if "vector" in extensions else "نصب نیست",
            ),
            ServicePart("متن‌های دانش", StatusLevel.OK if entries else StatusLevel.DEGRADED, fa(entries)),
        ]
        level = StatusLevel.OK
        if "pg_trgm" not in extensions:
            level = StatusLevel.DOWN
        elif "vector" not in extensions or not entries:
            level = StatusLevel.DEGRADED
        if self._settings.semantic_cache_enabled:
            model_ok = await asyncio.to_thread(Path(self._settings.semantic_cache_model_dir).exists)
            parts.append(
                ServicePart(
                    "مدل معنایی روی سرور",
                    StatusLevel.OK if model_ok else StatusLevel.DEGRADED,
                    "آماده" if model_ok else "پیدا نشد؛ پاسخ‌های هم‌معنی ذخیره نمی‌شوند",
                )
            )
            if not model_ok and level is StatusLevel.OK:
                level = StatusLevel.DEGRADED
        summary = "جست‌وجو آماده است." if level is StatusLevel.OK else "بخشی از جست‌وجوی دستیار کامل کار نمی‌کند."
        return ProbeResult(level, summary, tuple(parts))
