from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class CashClosing:
    """The count of the till at the end of one day against what the books say it should hold."""

    closing_id: uuid.UUID
    day: date
    expected_irr: int
    counted_irr: int
    entry_id: uuid.UUID | None  # the overage/shortage entry, when the count differed
    note: str
    closed_by: str
    created_at: datetime

    @property
    def difference_irr(self) -> int:
        return self.counted_irr - self.expected_irr
