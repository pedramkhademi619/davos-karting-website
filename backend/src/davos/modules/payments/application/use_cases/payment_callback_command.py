import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentCallbackCommand:
    """What the browser brought back. Nothing here is trusted: it only tells us which attempt to verify."""

    authority: str
    status_param: str
    customer_id: uuid.UUID
