from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from davos.composition.status.service_status import ServiceStatus
from davos.composition.status.status_level import StatusLevel


@dataclass(frozen=True)
class SystemStatusReport:
    overall: StatusLevel
    services: tuple[ServiceStatus, ...]
    checked_at: datetime
