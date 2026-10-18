from __future__ import annotations

from pydantic import BaseModel, Field


class AccountingReverseRequest(BaseModel):
    reason: str = Field(default="", max_length=200)
