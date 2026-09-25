import uuid
from dataclasses import dataclass

from davos.shared_kernel.domain.domain_event import DomainEvent


@dataclass(frozen=True, kw_only=True)
class PaymentReversed(DomainEvent):
    """Money that had been accepted for an order went back to the customer (the order must not stay paid)."""

    payment_id: uuid.UUID
    order_ref: str
    customer_id: uuid.UUID
    amount_irr: int
    was_paid: bool
