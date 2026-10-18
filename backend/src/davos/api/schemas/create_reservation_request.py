from __future__ import annotations

from datetime import date as Date  # noqa: N812 - a field is called date

from pydantic import BaseModel, Field


class CreateReservationRequest(BaseModel):
    date: Date
    time: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    single_count: int = Field(ge=0, le=50)
    double_count: int = Field(ge=0, le=50)
    contact_name: str = Field(default="", max_length=80)
