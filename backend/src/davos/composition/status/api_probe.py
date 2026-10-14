from __future__ import annotations

import platform
import time

from davos.composition.status.persian_text import duration
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.platform.settings.app_settings import AppSettings

_STARTED = time.monotonic()


class ApiProbe(ServiceProbe):
    key = "api"
    group = "برنامه"
    label = "سرور برنامه (API)"

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def check(self) -> ProbeResult:
        s = self._settings
        production = s.is_production
        parts = (
            ServicePart(
                "محیط",
                StatusLevel.OK if production else StatusLevel.TEST,
                "تولید (واقعی)" if production else "توسعه / آزمایشی",
            ),
            ServicePart("روشن بودن", StatusLevel.OK, duration(time.monotonic() - _STARTED)),
            ServicePart("پایتون", StatusLevel.OK, platform.python_version()),
            ServicePart(
                "کوکی امن (HTTPS)",
                StatusLevel.OK if s.cookie_secure else StatusLevel.TEST,
                "فعال" if s.cookie_secure else "غیرفعال",
            ),
            ServicePart(
                "نمایش کد پیامکی در API",
                StatusLevel.TEST if s.dev_sms_echo_enabled else StatusLevel.OK,
                "روشن (فقط توسعه)" if s.dev_sms_echo_enabled else "خاموش",
            ),
        )
        if production:
            return ProbeResult(StatusLevel.OK, "در حال اجرا (محیط واقعی).", parts)
        return ProbeResult(StatusLevel.TEST, "در حال اجرا در محیط آزمایشی/توسعه.", parts)
