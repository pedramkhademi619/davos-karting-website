import uuid

from pydantic import BaseModel, Field


class StartPaymentResponse(BaseModel):
    """Where to send the browser. For ``method == "POST"`` the page submits a form with ``form_fields``."""

    payment_id: uuid.UUID
    redirect_url: str
    method: str = "GET"
    form_fields: dict[str, str] = Field(default_factory=dict)
