from __future__ import annotations

from pydantic import BaseModel, Field


class AccountingVendorRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str = Field(default="", max_length=20)
    note: str = Field(default="", max_length=300)
    active: bool = True
