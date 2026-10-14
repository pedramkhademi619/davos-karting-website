from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class RevenueDay:
    day: date
    source: str
    amount_irr: int
