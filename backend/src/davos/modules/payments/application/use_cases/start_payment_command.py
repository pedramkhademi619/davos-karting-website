import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StartPaymentCommand:
    order_ref: str
    customer_id: uuid.UUID
