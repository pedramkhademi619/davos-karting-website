from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingPaymentRequest(BaseModel):
    """Paying a supplier (with ``vendor_id``) or handing a refund back to a customer (without)."""

    date: date
    from_account_id: str
    amount_toman: int = Field(gt=0, le=100_000_000_000_000)
    vendor_id: str | None = None
    description: str = Field(default="", max_length=300)
