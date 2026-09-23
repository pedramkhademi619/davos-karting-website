import uuid
from dataclasses import dataclass

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class PaymentSucceeded(DomainEvent):
    payment_id: uuid.UUID
    order_ref: str
    customer_id: uuid.UUID
    amount_irr: int
    reference_id: str
