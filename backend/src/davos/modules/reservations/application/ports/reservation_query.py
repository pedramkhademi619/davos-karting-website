from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus


@dataclass(frozen=True)
class ReservationQuery:
    date_from: date | None = None
    date_to: date | None = None
    status: ReservationStatus | None = None
    source: ReservationSource | None = None
    text: str = ""  # ticket code, name or mobile
    offset: int = 0
    limit: int = 50
