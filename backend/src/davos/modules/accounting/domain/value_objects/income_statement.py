from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.accounting.domain.value_objects.statement_line import StatementLine


@dataclass(frozen=True)
class IncomeStatement:
    date_from: date
    date_to: date
    revenue: tuple[StatementLine, ...]
    expenses: tuple[StatementLine, ...]

    @property
    def total_revenue(self) -> int:
        return sum(line.amount_irr for line in self.revenue)

    @property
    def total_expenses(self) -> int:
        return sum(line.amount_irr for line in self.expenses)

    @property
    def net_profit(self) -> int:
        return self.total_revenue - self.total_expenses
