from __future__ import annotations

import uuid

from davos.modules.booking.application.ports.booking_record_repository import BookingRecordRepository
from davos.modules.booking.application.use_cases.booking_return_status import BookingReturnStatus
from davos.modules.booking.domain.errors.booking_integration_disabled_error import BookingIntegrationDisabledError
from davos.shared_kernel.application.unit_of_work import UnitOfWork

PENDING_CONFIRMATION = "pending_confirmation"


class GetBookingReturnStatusUseCase:
    """The page a customer lands on after the booking system.

    The URL carries only a booking reference. Whether the booking succeeded is answered from our own
    verified data, so a forged or guessed return URL can never display a success.
    """

    def __init__(self, *, enabled: bool, uow: UnitOfWork, records: BookingRecordRepository) -> None:
        self._enabled = enabled
        self._uow = uow
        self._records = records

    async def execute(self, *, external_booking_id: str, user_id: uuid.UUID) -> BookingReturnStatus:
        if not self._enabled:
            raise BookingIntegrationDisabledError
        async with self._uow:
            record = await self._records.get_owned(external_booking_id, user_id)
        if record is None:  # not verified yet, or not this customer's: indistinguishable on purpose
            return BookingReturnStatus(state=PENDING_CONFIRMATION)
        return BookingReturnStatus(
            state=record.status.value, session_time=record.session_time, amount_irr=record.amount.irr
        )
