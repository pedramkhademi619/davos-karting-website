from __future__ import annotations

import uuid

from davos.modules.booking.application.ports.booking_record_repository import BookingRecordRepository
from davos.modules.booking.domain.entities.booking_record import BookingRecord


class InMemoryBookingRecordRepository(BookingRecordRepository):
    def __init__(self) -> None:
        self.items: dict[str, BookingRecord] = {}
        self.fail_next_add = False

    async def get_for_update(self, external_booking_id: str) -> BookingRecord | None:
        return self.items.get(external_booking_id)

    async def add(self, record: BookingRecord) -> None:
        if self.fail_next_add:
            self.fail_next_add = False
            raise ConnectionError("database unavailable")
        self.items[record.external_booking_id] = record

    async def save(self, record: BookingRecord) -> None:
        self.items[record.external_booking_id] = record

    async def get_owned(self, external_booking_id: str, user_id: uuid.UUID) -> BookingRecord | None:
        record = self.items.get(external_booking_id)
        return record if record and record.user_id == user_id else None
