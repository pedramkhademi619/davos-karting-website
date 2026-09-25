from __future__ import annotations

from datetime import date

from davos.modules.reservations.application.ports.reservation_stats import ReservationStats
from davos.modules.reservations.application.ports.reservation_stats_reader import ReservationStatsReader
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetReservationStatsUseCase:
    def __init__(self, *, uow: UnitOfWork, stats: ReservationStatsReader) -> None:
        self._uow = uow
        self._stats = stats

    async def execute(self, date_from: date, date_to: date) -> ReservationStats:
        async with self._uow:
            return await self._stats.stats(date_from, date_to)
