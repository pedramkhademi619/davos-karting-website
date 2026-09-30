from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class StaffUpdateReservationUseCase:
    """Staff actions on one reservation: cancel it, or check the customer in."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository, clock: Clock) -> None:
        self._uow = uow
        self._reservations = reservations
        self._clock = clock

    async def cancel(self, reservation_id: uuid.UUID, reason: str) -> Reservation:
        async with self._uow:
            reservation = await self._load(reservation_id)
            reservation.cancel(reason=reason or "لغو توسط مجموعه", by_staff=True, now=self._clock.now())
            return await self._store(reservation)

    async def mark_attended(self, reservation_id: uuid.UUID) -> Reservation:
        async with self._uow:
            reservation = await self._load(reservation_id)
            reservation.mark_attended(self._clock.now())
            return await self._store(reservation)

    async def _load(self, reservation_id: uuid.UUID) -> Reservation:
        reservation = await self._reservations.get_for_update(reservation_id)
        if reservation is None:
            raise ReservationNotFoundError
        return reservation

    async def _store(self, reservation: Reservation) -> Reservation:
        await self._reservations.save(reservation)
        self._uow.collect_events(reservation.pull_events())
        await self._uow.commit()
        return reservation
