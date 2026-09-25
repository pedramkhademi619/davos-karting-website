from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_page import ReservationPage
from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class SearchReservationsUseCase:
    """Staff view of reservations (the reservation list and a single ticket)."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository) -> None:
        self._uow = uow
        self._reservations = reservations

    async def execute(self, query: ReservationQuery) -> ReservationPage:
        async with self._uow:
            return await self._reservations.search(query)

    async def one(self, reservation_id: uuid.UUID) -> Reservation | None:
        async with self._uow:
            return await self._reservations.get(reservation_id)
