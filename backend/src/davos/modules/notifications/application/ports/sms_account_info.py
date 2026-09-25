from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SmsAccountInfo:
    remaining_credit_irr: int
    expires_at: datetime | None
    account_type: str
