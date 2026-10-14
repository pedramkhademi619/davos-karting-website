from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Sequence

from davos.composition.status.probe_result import ProbeResult
from davos.composition.status.service_probe import ServiceProbe
from davos.composition.status.service_status import ServiceStatus
from davos.composition.status.status_level import StatusLevel
from davos.composition.status.system_status_report import SystemStatusReport
from davos.shared_kernel.application.clock import Clock

logger = logging.getLogger(__name__)

_PROBE_TIMEOUT_SECONDS = 8.0


class SystemStatusService:
    """Runs every probe at the same time; a slow or broken probe is reported as down, never as an error."""

    def __init__(self, probes: Sequence[ServiceProbe], clock: Clock) -> None:
        self._probes = tuple(probes)
        self._clock = clock
        self._cache: dict[str, tuple[float, ProbeResult]] = {}

    async def report(self) -> SystemStatusReport:
        results = await asyncio.gather(*(self._run(p) for p in self._probes))
        now = self._clock.now()
        services = tuple(
            ServiceStatus(
                key=p.key,
                group=p.group,
                label=p.label,
                level=r.level,
                summary=r.summary,
                latency_ms=r.latency_ms,
                parts=r.parts,
                checked_at=now,
            )
            for p, r in zip(self._probes, results, strict=True)
        )
        return SystemStatusReport(overall=self.overall(services), services=services, checked_at=now)

    @staticmethod
    def overall(services: Sequence[ServiceStatus]) -> StatusLevel:
        levels = {s.level for s in services}
        if StatusLevel.DOWN in levels:
            return StatusLevel.DOWN
        if StatusLevel.DEGRADED in levels:
            return StatusLevel.DEGRADED
        return StatusLevel.OK

    async def _run(self, probe: ServiceProbe) -> ProbeResult:
        cached = self._cache.get(probe.key)
        if probe.cache_seconds and cached and time.monotonic() - cached[0] < probe.cache_seconds:
            return cached[1]
        started = time.monotonic()
        try:
            result = await asyncio.wait_for(probe.check(), timeout=_PROBE_TIMEOUT_SECONDS)
        except TimeoutError:
            result = ProbeResult(StatusLevel.DOWN, "پاسخی در مهلت مقرر نیامد.")
        except Exception as exc:  # a probe must never break the page
            logger.warning("status probe %s failed: %s", probe.key, type(exc).__name__)
            result = ProbeResult(StatusLevel.DOWN, f"بررسی انجام نشد ({type(exc).__name__}).")
        if result.latency_ms is None:
            result = ProbeResult(result.level, result.summary, result.parts, int((time.monotonic() - started) * 1000))
        if probe.cache_seconds:
            self._cache[probe.key] = (time.monotonic(), result)
        return result
