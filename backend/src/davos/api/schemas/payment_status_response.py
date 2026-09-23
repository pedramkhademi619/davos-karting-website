import uuid

from pydantic import BaseModel


class PaymentStatusResponse(BaseModel):
    payment_id: uuid.UUID
    status: str
    amount_irr: int | None = None
    amount_toman: int | None = None
    reference_id: str | None = None
