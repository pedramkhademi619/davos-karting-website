from __future__ import annotations

import uuid

from sqlalchemy import select, update

from davos.modules.booking.adapters.persistence.booking_record_mapper import BookingRecordMapper
from davos.modules.booking.adapters.persistence.booking_record_model import BookingRecordModel
from davos.modules.booking.application.ports.booking_record_repository import BookingRecordRepository
from davos.modules.booking.domain.entities.booking_record import BookingRecord
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyBookingRecordRepository(BookingRecordRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get_for_update(self, external_booking_id: str) -> BookingRecord | None:
        result = await self._uow.session.execute(
            select(BookingRecordModel)
            .where(BookingRecordModel.external_booking_id == external_booking_id)
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return BookingRecordMapper.to_domain(model) if model else None

    async def add(self, record: BookingRecord) -> None:
        self._uow.session.add(BookingRecordMapper.to_model(record))
        await self._uow.session.flush()

    async def save(self, record: BookingRecord) -> None:
        await self._uow.session.execute(
            update(BookingRecordModel)
            .where(BookingRecordModel.id == record.id)
            .values(
                status=record.status.value,
                amount_irr=record.amount.irr,
                session_time=record.session_time,
                last_updated_at=record.last_updated_at,
                last_event_id=record.last_event_id,
            )
        )

    async def get_owned(self, external_booking_id: str, user_id: uuid.UUID) -> BookingRecord | None:
        result = await self._uow.session.execute(
            select(BookingRecordModel).where(
                BookingRecordModel.external_booking_id == external_booking_id, BookingRecordModel.user_id == user_id
            )
        )
        model = result.scalar_one_or_none()
        return BookingRecordMapper.to_domain(model) if model else None
