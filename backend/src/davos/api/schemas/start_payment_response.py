import uuid

from pydantic import BaseModel


class StartPaymentResponse(BaseModel):
    payment_id: uuid.UUID
    redirect_url: str
