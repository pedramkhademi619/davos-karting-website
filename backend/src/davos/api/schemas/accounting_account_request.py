from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AccountingAccountRequest(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=120)
    type: Literal["asset", "liability", "equity", "revenue", "expense"] = "expense"
    parent_id: str | None = None
    is_group: bool = False
    active: bool = True
