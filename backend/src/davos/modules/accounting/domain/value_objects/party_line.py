from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PartyLine:
    party_id: uuid.UUID
    entry_date: date
    debit_irr: int
    credit_irr: int
