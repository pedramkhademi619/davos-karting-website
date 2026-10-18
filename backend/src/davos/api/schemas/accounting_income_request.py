from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingIncomeRequest(BaseModel):
    date: date
    revenue_account_id: str
    amount_toman: int = Field(gt=0, le=100_000_000_000_000)
    vat_toman: int = Field(default=0, ge=0, le=100_000_000_000_000)
    deposit_account_id: str
    description: str = Field(default="", max_length=300)
