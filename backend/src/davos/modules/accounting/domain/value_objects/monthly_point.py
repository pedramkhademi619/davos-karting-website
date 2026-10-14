from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyPoint:
    key: str  # "1405-07"
    revenue_irr: int
    expenses_irr: int

    @property
    def profit_irr(self) -> int:
        return self.revenue_irr - self.expenses_irr
