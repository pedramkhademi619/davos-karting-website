from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class AccountingSettingsRequest(BaseModel):
    auto_posting_enabled: bool
    vat_percent: int = Field(ge=0, le=30)
    gateway_fee_percent: float = Field(ge=0, le=10)
    revenue_recognition: Literal["on_payment", "on_session"]
    locked_through: date | None = None
