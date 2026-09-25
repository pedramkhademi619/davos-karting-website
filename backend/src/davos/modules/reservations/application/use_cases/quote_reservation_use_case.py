from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.use_cases.reservation_quote import ReservationQuote
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class QuoteReservationUseCase:
    """The trusted amount of a held reservation, for the payment module. None when it cannot be paid (any more)."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository, clock: Clock) -> None:
        self._uow = uow
        self._reservations = reservations
        self._clock = clock

    async def execute(self, reservation_id: uuid.UUID, customer_id: uuid.UUID) -> ReservationQuote | None:
        async with self._uow:
            reservation = await self._reservations.get(reservation_id)
        if reservation is None or reservation.customer_id != customer_id:
            return None
        if reservation.status is not ReservationStatus.HELD or not reservation.occupies_seats_at(self._clock.now()):
            return None
        return ReservationQuote(
            amount=reservation.amount,
            description=f"رزرو سانس کارتینگ داوس {reservation.code}",
        )
