from __future__ import annotations

import time

import httpx

from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_part import ServicePart
from davos.composition.status.status_level import StatusLevel

_SLOW_MS = 2500


async def probe_url(url: str, *, wait_seconds: float = 5.0) -> ProbeResult:
    """Does something answer at this address? Any HTTP answer below 500 counts (a login-protected API says 401)."""
    if "://" not in url:
        url = f"https://{url}"
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=wait_seconds, follow_redirects=False) as client:
            response = await client.get(url)
    except httpx.TimeoutException:
        return ProbeResult(StatusLevel.DOWN, "پاسخی نمی‌دهد (زمان انتظار تمام شد).")
    except httpx.HTTPError as exc:
        return ProbeResult(StatusLevel.DOWN, f"وصل نمی‌شود ({type(exc).__name__}).")
    latency = int((time.monotonic() - started) * 1000)
    host = httpx.URL(url).host
    parts = (
        ServicePart("آدرس", StatusLevel.OK, host),
        ServicePart("کد پاسخ", StatusLevel.OK, str(response.status_code)),
    )
    if response.status_code >= 500:
        return ProbeResult(StatusLevel.DEGRADED, "سرور مقصد خطا می‌دهد.", parts, latency)
    if latency > _SLOW_MS:
        return ProbeResult(StatusLevel.DEGRADED, "در دسترس است ولی کند.", parts, latency)
    return ProbeResult(StatusLevel.OK, "در دسترس است.", parts, latency)
