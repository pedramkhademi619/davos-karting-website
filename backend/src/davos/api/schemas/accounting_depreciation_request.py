from __future__ import annotations

from pydantic import BaseModel, Field


class AccountingDepreciationRequest(BaseModel):
    year: int = Field(ge=1300, le=1600)
    month: int = Field(ge=1, le=12)
