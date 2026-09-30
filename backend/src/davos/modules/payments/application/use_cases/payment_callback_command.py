import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentCallbackCommand:
    """What the browser brought back. Nothing here is trusted: it only tells us which attempt to verify.

    ``customer_id`` is None for gateways that return with a cross-site POST (Mellat): the session cookie is not sent
    then, and it does not need to be, because the outcome is decided by server-to-server verification only.
    """

    authority: str
    succeeded: bool
    customer_id: uuid.UUID | None = None
    gateway_order_id: int | None = None
    provider_reference: str | None = None
    provider_code: str | None = None
