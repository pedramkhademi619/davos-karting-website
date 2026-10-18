from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from davos.api.schemas.service_part_response import ServicePartResponse
from davos.composition.status.service_status import ServiceStatus


class ServiceStatusResponse(BaseModel):
    key: str
    group: str
    label: str
    level: str
    summary: str
    latency_ms: int | None
    parts: list[ServicePartResponse]
    checked_at: datetime

    @classmethod
    def of(cls, status: ServiceStatus) -> ServiceStatusResponse:
        return cls(
            key=status.key,
            group=status.group,
            label=status.label,
            level=status.level.value,
            summary=status.summary,
            latency_ms=status.latency_ms,
            parts=[ServicePartResponse(label=p.label, level=p.level.value, detail=p.detail) for p in status.parts],
            checked_at=status.checked_at,
        )
