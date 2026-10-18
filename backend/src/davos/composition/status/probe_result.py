from __future__ import annotations

from dataclasses import dataclass

from davos.composition.status.service_part import ServicePart
from davos.composition.status.status_level import StatusLevel


@dataclass(frozen=True)
class ProbeResult:
    level: StatusLevel
    summary: str
    parts: tuple[ServicePart, ...] = ()
    latency_ms: int | None = None
