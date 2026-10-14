from __future__ import annotations

from pydantic import BaseModel, Field


class AccountingJournalLineRequest(BaseModel):
    account_id: str
    debit_toman: int = Field(default=0, ge=0, le=100_000_000_000_000)
    credit_toman: int = Field(default=0, ge=0, le=100_000_000_000_000)
    memo: str = Field(default="", max_length=300)
    vendor_id: str | None = None
