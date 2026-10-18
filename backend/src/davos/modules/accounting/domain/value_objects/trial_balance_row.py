from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class TrialBalanceRow:
    account_id: uuid.UUID
    code: str
    name: str
    account_type: str
    opening_debit: int
    opening_credit: int
    debit: int
    credit: int
    closing_debit: int
    closing_credit: int
