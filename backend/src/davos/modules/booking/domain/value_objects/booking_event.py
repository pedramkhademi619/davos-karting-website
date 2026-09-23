from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class BookingEvent:
    """Validated webhook payload (the booking system's contract)."""

    event_id: str
    external_booking_id: str
    user_id: uuid.UUID
    status: BookingStatus
    amount: Money
    session_time: datetime
    updated_at: datetime
