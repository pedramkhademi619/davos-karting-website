from __future__ import annotations

from dataclasses import dataclass

from davos.modules.reservations.domain.entities.reservation import Reservation


@dataclass(frozen=True)
class ReservationPage:
    items: list[Reservation]
    total: int
