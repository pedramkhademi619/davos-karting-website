from __future__ import annotations

from davos.composition.status.http_reachability import probe_url
from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.status_level import StatusLevel


class HttpServiceProbe(ServiceProbe):
    """One of our own services that answers HTTP inside the deployment (the website, the game)."""

    group = "برنامه"

    def __init__(self, *, key: str, label: str, url: str) -> None:
        self.key = key
        self.label = label
        self._url = url

    async def check(self) -> ProbeResult:
        if not self._url:
            return ProbeResult(StatusLevel.DISABLED, "آدرس بررسی تنظیم نشده است.")
        return await probe_url(self._url, wait_seconds=4.0)
