from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class AccountingAssetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    asset_account_id: str
    cost_toman: int = Field(gt=0, le=100_000_000_000_000)
    salvage_toman: int = Field(default=0, ge=0, le=100_000_000_000_000)
    in_service_date: date
    life_months: int = Field(ge=1, le=600)
    note: str = Field(default="", max_length=300)
    post_purchase: bool = True
    paid_from_account_id: str | None = None
    vendor_id: str | None = None
