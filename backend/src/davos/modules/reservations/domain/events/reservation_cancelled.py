import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ReservationCancelled(DomainEvent):
    reservation_id: uuid.UUID
    customer_id: uuid.UUID | None
    code: str
    starts_at: datetime
    was_paid: bool
    reason: str
