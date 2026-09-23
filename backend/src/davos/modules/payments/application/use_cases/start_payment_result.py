import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StartPaymentResult:
    payment_id: uuid.UUID
    redirect_url: str
