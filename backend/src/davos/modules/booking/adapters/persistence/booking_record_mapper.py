from __future__ import annotations

from davos.modules.booking.adapters.persistence.booking_record_model import BookingRecordModel
from davos.modules.booking.domain.entities.booking_record import BookingRecord
from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.shared_kernel.domain.money import Money


class BookingRecordMapper:
    @staticmethod
    def to_domain(model: BookingRecordModel) -> BookingRecord:
        return BookingRecord(
            record_id=model.id,
            external_booking_id=model.external_booking_id,
            user_id=model.user_id,
            status=BookingStatus(model.status),
            amount=Money(model.amount_irr),
            session_time=model.session_time,
            last_updated_at=model.last_updated_at,
            last_event_id=model.last_event_id,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(record: BookingRecord) -> BookingRecordModel:
        return BookingRecordModel(
            id=record.id,
            external_booking_id=record.external_booking_id,
            user_id=record.user_id,
            status=record.status.value,
            amount_irr=record.amount.irr,
            session_time=record.session_time,
            last_updated_at=record.last_updated_at,
            last_event_id=record.last_event_id,
            created_at=record.created_at,
        )
