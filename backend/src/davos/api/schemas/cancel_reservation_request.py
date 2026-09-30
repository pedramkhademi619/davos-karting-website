from pydantic import BaseModel, Field


class CancelReservationRequest(BaseModel):
    reason: str = Field(default="", max_length=300)
