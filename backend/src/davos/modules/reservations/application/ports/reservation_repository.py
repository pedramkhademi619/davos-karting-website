from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime, time

from davos.modules.reservations.application.ports.reservation_page import ReservationPage
from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.value_objects.daily_online_load import DailyOnlineLoad
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad


class ReservationRepository(ABC):
    @abstractmethod
    async def next_ticket_number(self) -> int:
        """A fresh, race-free ticket number from the database sequence (starts at 100). Pulled before the entity
        is constructed, the same pattern as the payments module's gateway order id."""

    @abstractmethod
    async def add(self, reservation: Reservation) -> None: ...

    @abstractmethod
    async def save(self, reservation: Reservation) -> None: ...

    @abstractmethod
    async def get_for_update(self, reservation_id: uuid.UUID) -> Reservation | None: ...

    @abstractmethod
    async def get(self, reservation_id: uuid.UUID) -> Reservation | None: ...

    @abstractmethod
    async def lock_session(self, day: date, session_time: time) -> None:
        """Serialise bookings of one session until the transaction ends, so two customers never get the last kart."""

    @abstractmethod
    async def session_load(self, day: date, session_time: time, now: datetime) -> SessionLoad: ...

    @abstractmethod
    async def day_loads(self, day: date, now: datetime) -> dict[time, SessionLoad]: ...

    @abstractmethod
    async def lock_day(self, day: date) -> None:
        """Serialises every online booking of one business day, for the owner's optional daily cap (people or
        tickets). Always taken before ``lock_session`` when both are needed, so the two can never deadlock."""

    @abstractmethod
    async def day_online_load(self, day: date, now: datetime) -> DailyOnlineLoad:
        """Today's online bookings only (``source="online"``) that occupy a seat right now."""

    @abstractmethod
    async def count_active_holds(self, customer_id: uuid.UUID, now: datetime) -> int: ...

    @abstractmethod
    async def list_for_customer(self, customer_id: uuid.UUID, *, limit: int) -> list[Reservation]: ...

    @abstractmethod
    async def search(self, query: ReservationQuery) -> ReservationPage: ...

    @abstractmethod
    async def list_overdue_holds(self, now: datetime, *, limit: int) -> list[uuid.UUID]: ...
