from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SessionAvailabilityResponse(BaseModel):
    time: str
    starts_at: datetime
    singles_left: int
    doubles_left: int
    single_capacity: int
    double_capacity: int
    bookable: bool
