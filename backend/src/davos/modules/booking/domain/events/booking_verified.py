import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class BookingVerified(DomainEvent):
    """First verified sighting of a booking. Loyalty, notifications and history react to it."""

    external_booking_id: str
    user_id: uuid.UUID
    status: str
    amount_irr: int
    session_time: datetime
