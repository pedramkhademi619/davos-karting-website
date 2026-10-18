from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class LedgerLine:
    entry_id: uuid.UUID
    entry_number: int
    fiscal_year: int
    entry_date: date
    description: str
    memo: str
    debit_irr: int
    credit_irr: int
    source: str
    party_id: uuid.UUID | None
