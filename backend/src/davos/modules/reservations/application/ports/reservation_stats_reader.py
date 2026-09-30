from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from davos.modules.reservations.application.ports.reservation_stats import ReservationStats


class ReservationStatsReader(ABC):
    @abstractmethod
    async def stats(self, date_from: date, date_to: date) -> ReservationStats: ...
