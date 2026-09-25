from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class CancelOwnHoldUseCase:
    """A customer can release seats they have not paid for yet. Paid reservations are cancelled by staff only."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository, clock: Clock) -> None:
        self._uow = uow
        self._reservations = reservations
        self._clock = clock

    async def execute(self, *, customer_id: uuid.UUID, reservation_id: uuid.UUID) -> None:
        async with self._uow:
            reservation = await self._reservations.get_for_update(reservation_id)
            if reservation is None or reservation.customer_id != customer_id:
                raise ReservationNotFoundError
            reservation.cancel(reason="انصراف مشتری پیش از پرداخت", by_staff=False, now=self._clock.now())
            await self._reservations.save(reservation)
            self._uow.collect_events(reservation.pull_events())
            await self._uow.commit()
