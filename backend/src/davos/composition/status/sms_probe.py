from __future__ import annotations

from collections.abc import Awaitable, Callable

from davos.composition.status.persian_text import fa
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo

_LOW_CREDIT_TOMAN = 50_000


class SmsProbe(ServiceProbe):
    key = "sms"
    group = "سرویس‌های بیرونی"
    label = "پیامک"
    cache_seconds = 60.0

    def __init__(
        self, *, provider: str, is_test_gateway: bool, account: Callable[[], Awaitable[SmsAccountInfo | None]]
    ) -> None:
        self._provider = provider
        self._is_test_gateway = is_test_gateway
        self._account = account

    async def check(self) -> ProbeResult:
        if self._is_test_gateway:
            return ProbeResult(
                StatusLevel.TEST,
                "حالت آزمایشی: پیامکی واقعاً ارسال نمی‌شود (کدها فقط در پاسخ API دیده می‌شوند).",
                (ServicePart("ارائه‌دهنده", StatusLevel.TEST, self._provider or "آزمایشی"),),
            )
        info = await self._account()
        if info is None:
            return ProbeResult(
                StatusLevel.DOWN,
                "اتصال به پنل پیامک برقرار نشد یا کلید نامعتبر است.",
                (ServicePart("ارائه‌دهنده", StatusLevel.DOWN, self._provider),),
            )
        credit = info.remaining_credit_irr // 10
        parts = [
            ServicePart("ارائه‌دهنده", StatusLevel.OK, self._provider),
            ServicePart(
                "اعتبار باقی‌مانده",
                StatusLevel.DEGRADED if credit < _LOW_CREDIT_TOMAN else StatusLevel.OK,
                f"{fa(f'{credit:,}')} تومان",
            ),
        ]
        if info.expires_at is not None:
            parts.append(ServicePart("انقضای حساب", StatusLevel.OK, fa(info.expires_at.date().isoformat())))
        if credit < _LOW_CREDIT_TOMAN:
            return ProbeResult(StatusLevel.DEGRADED, "اعتبار پیامک کم است؛ شارژ کنید.", tuple(parts))
        return ProbeResult(StatusLevel.OK, "متصل است.", tuple(parts))
