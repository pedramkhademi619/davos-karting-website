from __future__ import annotations

from davos.composition.status.http_reachability import probe_url
from davos.composition.status.persian_text import fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.platform.settings.app_settings import AppSettings


class AiProbe(ServiceProbe):
    key = "ai"
    group = "سرویس‌های بیرونی"
    label = "هوش مصنوعی دستیار"
    cache_seconds = 60.0

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def check(self) -> ProbeResult:
        s = self._settings
        if not s.ai_base_url or not s.ai_api_key.get_secret_value() or not s.ai_model:
            return ProbeResult(
                StatusLevel.DISABLED, "ارائه‌دهنده هوش مصنوعی تنظیم نشده؛ دستیار فقط پاسخ‌های آماده و ذخیره‌شده می‌دهد."
            )
        reach = await probe_url(s.ai_base_url)
        parts = [
            ServicePart("مدل", StatusLevel.OK, s.ai_model),
            ServicePart("مدل جایگزین", StatusLevel.OK, s.ai_fallback_model or "—"),
            ServicePart("سقف توکن روزانه", StatusLevel.OK, fa(f"{s.ai_daily_token_budget:,}")),
            *reach.parts,
        ]
        summary = {
            StatusLevel.OK: "ارائه‌دهنده در دسترس است.",
            StatusLevel.DEGRADED: "ارائه‌دهنده کند است یا خطا می‌دهد؛ دستیار ممکن است پاسخ آماده بدهد.",
            StatusLevel.DOWN: "ارائه‌دهنده در دسترس نیست؛ دستیار فقط از پاسخ‌های آماده و ذخیره‌شده استفاده می‌کند.",
        }[reach.level]
        return ProbeResult(reach.level, summary, tuple(parts), reach.latency_ms)
