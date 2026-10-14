from __future__ import annotations

from dataclasses import dataclass

from davos.composition.status.status_level import StatusLevel


@dataclass(frozen=True)
class ServicePart:
    """One line under a service, e.g. one background job or one table."""

    label: str
    level: StatusLevel
    detail: str = ""
