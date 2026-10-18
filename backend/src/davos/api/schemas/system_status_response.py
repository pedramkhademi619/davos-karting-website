from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from davos.api.schemas.service_status_response import ServiceStatusResponse
from davos.composition.status.system_status_report import SystemStatusReport


class SystemStatusResponse(BaseModel):
    overall: str
    checked_at: datetime
    services: list[ServiceStatusResponse]

    @classmethod
    def of(cls, report: SystemStatusReport) -> SystemStatusResponse:
        return cls(
            overall=report.overall.value,
            checked_at=report.checked_at,
            services=[ServiceStatusResponse.of(s) for s in report.services],
        )
