from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingCashClosingRequest(BaseModel):
    date: date
    counted_toman: int = Field(ge=0, le=100_000_000_000_000)
    note: str = Field(default="", max_length=300)
