from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingTransferRequest(BaseModel):
    date: date
    from_account_id: str
    to_account_id: str
    amount_toman: int = Field(gt=0, le=100_000_000_000_000)
    description: str = Field(default="", max_length=300)
