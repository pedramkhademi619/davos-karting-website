from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AccountingStaffPayRequest(BaseModel):
    kind: Literal["salary", "advance", "bonus"] = "salary"
    amount_toman: int = Field(gt=0, le=100_000_000_000)
    date: date
    paid_from_account_id: str
    note: str = Field(default="", max_length=300)
