from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingExpenseRequest(BaseModel):
    date: date
    expense_account_id: str
    amount_toman: int = Field(gt=0, le=100_000_000_000_000)
    vat_toman: int = Field(default=0, ge=0, le=100_000_000_000_000)
    paid_from_account_id: str | None = None  # None = on credit, owed to the vendor
    vendor_id: str | None = None
    description: str = Field(default="", max_length=300)
