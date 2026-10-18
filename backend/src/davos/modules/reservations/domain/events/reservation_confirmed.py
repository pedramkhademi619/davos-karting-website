import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class ReservationConfirmed(DomainEvent):
    reservation_id: uuid.UUID
    customer_id: uuid.UUID | None
    code: str
    starts_at: datetime
    single_count: int
    double_count: int
    amount_irr: int
    source: str
    confirmed_late: bool
