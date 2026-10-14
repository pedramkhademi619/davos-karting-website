from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from davos.composition.status.service_part import ServicePart
from davos.composition.status.status_level import StatusLevel


@dataclass(frozen=True)
class ServiceStatus:
    key: str
    group: str
    label: str
    level: StatusLevel
    summary: str
    latency_ms: int | None
    parts: tuple[ServicePart, ...]
    checked_at: datetime
