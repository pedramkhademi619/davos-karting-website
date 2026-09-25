from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetCustomerReservationsUseCase:
    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository) -> None:
        self._uow = uow
        self._reservations = reservations

    async def for_customer(self, customer_id: uuid.UUID, *, limit: int = 50) -> list[Reservation]:
        async with self._uow:
            return await self._reservations.list_for_customer(customer_id, limit=limit)

    async def one(self, customer_id: uuid.UUID, reservation_id: uuid.UUID) -> Reservation:
        async with self._uow:
            reservation = await self._reservations.get(reservation_id)
        if reservation is None or reservation.customer_id != customer_id:
            raise ReservationNotFoundError
        return reservation
