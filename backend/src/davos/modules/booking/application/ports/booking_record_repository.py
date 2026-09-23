from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.booking.domain.entities.booking_record import BookingRecord


class BookingRecordRepository(ABC):
    @abstractmethod
    async def get_for_update(self, external_booking_id: str) -> BookingRecord | None: ...

    @abstractmethod
    async def add(self, record: BookingRecord) -> None: ...

    @abstractmethod
    async def save(self, record: BookingRecord) -> None: ...

    @abstractmethod
    async def get_owned(self, external_booking_id: str, user_id: uuid.UUID) -> BookingRecord | None: ...
