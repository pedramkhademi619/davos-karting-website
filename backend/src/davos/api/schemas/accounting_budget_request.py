from __future__ import annotations

from pydantic import BaseModel, Field


class AccountingBudgetRequest(BaseModel):
    account_id: str
    year: int = Field(ge=1300, le=1600)
    month: int | None = Field(default=None, ge=1, le=12)  # None = the amount is for the whole year, spread evenly
    amount_toman: int = Field(ge=0, le=100_000_000_000_000)
