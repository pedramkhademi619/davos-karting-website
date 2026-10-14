from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class StatementLine:
    account_id: uuid.UUID | None
    code: str
    name: str
    group: str
    amount_irr: int
