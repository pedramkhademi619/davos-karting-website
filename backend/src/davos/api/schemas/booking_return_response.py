from datetime import datetime

from pydantic import BaseModel


class BookingReturnResponse(BaseModel):
    state: str
    message: str
    session_time: datetime | None
    amount_irr: int | None
