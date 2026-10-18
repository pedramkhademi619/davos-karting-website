from __future__ import annotations

from davos.composition.status.http_reachability import probe_url
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel
from davos.platform.settings.app_settings import AppSettings

_NAMES = {"mellat": "بانک ملت (به‌پرداخت)", "zarinpal": "زرین‌پال"}


class PaymentGatewayProbe(ServiceProbe):
    key = "payment_gateway"
    group = "سرویس‌های بیرونی"
    label = "درگاه پرداخت"
    cache_seconds = 60.0

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    async def check(self) -> ProbeResult:
        s = self._settings
        name = _NAMES.get(s.payment_provider, s.payment_provider)
        if not s.payments_enabled:
            return ProbeResult(
                StatusLevel.DISABLED,
                "پرداخت آنلاین خاموش است؛ رزرو آنلاین نمی‌تواند پرداخت بگیرد.",
                (ServicePart("درگاه تنظیم‌شده", StatusLevel.DISABLED, name),),
            )
        sandbox = s.payment_provider == "zarinpal" and s.zarinpal_sandbox
        if s.payment_provider == "zarinpal":
            url = s.zarinpal_sandbox_host if sandbox else s.zarinpal_api_host
        else:
            url = s.mellat_service_url
        reach = await probe_url(url)
        parts = [
            ServicePart("درگاه", StatusLevel.OK, name),
            ServicePart(
                "حالت", StatusLevel.TEST if sandbox else StatusLevel.OK, "آزمایشی (Sandbox)" if sandbox else "واقعی"
            ),
            ServicePart("آدرس بازگشت از بانک", StatusLevel.OK, s.effective_payment_callback_url),
            *reach.parts,
        ]
        if reach.level is StatusLevel.OK and sandbox:
            return ProbeResult(
                StatusLevel.TEST, "درگاه آزمایشی در دسترس است؛ پول واقعی جابه‌جا نمی‌شود.", tuple(parts), reach.latency_ms
            )
        summary = {
            StatusLevel.OK: "درگاه در دسترس است.",
            StatusLevel.DEGRADED: "درگاه کند است یا خطا می‌دهد.",
            StatusLevel.DOWN: "درگاه در دسترس نیست؛ مشتری نمی‌تواند پرداخت کند.",
        }[reach.level]
        return ProbeResult(reach.level, summary, tuple(parts), reach.latency_ms)
