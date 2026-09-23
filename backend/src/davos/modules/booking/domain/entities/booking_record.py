from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.booking.domain.enums.apply_result import ApplyResult
from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.modules.booking.domain.errors.booking_owner_mismatch_error import BookingOwnerMismatchError
from davos.modules.booking.domain.events.booking_status_changed import BookingStatusChanged
from davos.modules.booking.domain.events.booking_verified import BookingVerified
from davos.modules.booking.domain.value_objects.booking_event import BookingEvent
from davos.shared_kernel.domain.aggregate_root import AggregateRoot
from davos.shared_kernel.domain.money import Money


class BookingRecord(AggregateRoot[uuid.UUID]):
    """Local copy of a booking, created and changed only from *verified* events of the booking system."""

    def __init__(
        self,
        *,
        record_id: uuid.UUID,
        external_booking_id: str,
        user_id: uuid.UUID,
        status: BookingStatus,
        amount: Money,
        session_time: datetime,
        last_updated_at: datetime,
        last_event_id: str,
        created_at: datetime,
    ) -> None:
        super().__init__(record_id)
        self.external_booking_id = external_booking_id
        self.user_id = user_id
        self.status = status
        self.amount = amount
        self.session_time = session_time
        self.last_updated_at = last_updated_at
        self.last_event_id = last_event_id
        self.created_at = created_at

    @classmethod
    def from_event(cls, event: BookingEvent, now: datetime) -> BookingRecord:
        record = cls(
            record_id=uuid.uuid4(),
            external_booking_id=event.external_booking_id,
            user_id=event.user_id,
            status=event.status,
            amount=event.amount,
            session_time=event.session_time,
            last_updated_at=event.updated_at,
            last_event_id=event.event_id,
            created_at=now,
        )
        record._raise(
            BookingVerified(
                external_booking_id=event.external_booking_id,
                user_id=event.user_id,
                status=event.status.value,
                amount_irr=event.amount.irr,
                session_time=event.session_time,
                occurred_at=now,
            )
        )
        return record

    def apply(self, event: BookingEvent, now: datetime) -> ApplyResult:
        """Apply a newer event. Older or equal ones (out-of-order or replayed delivery) are ignored."""
        if event.user_id != self.user_id:
            raise BookingOwnerMismatchError
        if event.updated_at <= self.last_updated_at:
            return ApplyResult.STALE_IGNORED
        previous = self.status
        self.status = event.status
        self.amount = event.amount
        self.session_time = event.session_time
        self.last_updated_at = event.updated_at
        self.last_event_id = event.event_id
        if previous is not event.status:
            self._raise(
                BookingStatusChanged(
                    external_booking_id=self.external_booking_id,
                    user_id=self.user_id,
                    previous_status=previous.value,
                    status=event.status.value,
                    amount_irr=event.amount.irr,
                    occurred_at=now,
                )
            )
        return ApplyResult.APPLIED
