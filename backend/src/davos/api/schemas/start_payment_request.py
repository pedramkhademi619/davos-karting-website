from pydantic import BaseModel, ConfigDict, Field


class StartPaymentRequest(BaseModel):
    """Only an order reference is accepted. There is deliberately no amount field: prices are server-side."""

    model_config = ConfigDict(extra="forbid")

    order_ref: str = Field(min_length=1, max_length=100)
