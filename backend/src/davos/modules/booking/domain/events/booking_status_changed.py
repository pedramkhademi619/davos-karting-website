import uuid
from dataclasses import dataclass

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class BookingStatusChanged(DomainEvent):
    external_booking_id: str
    user_id: uuid.UUID
    previous_status: str
    status: str
    amount_irr: int
