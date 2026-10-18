from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SmsAccountResponse(BaseModel):
    provider: str
    connected: bool
    remaining_credit_toman: int | None = None
    expires_at: datetime | None = None
