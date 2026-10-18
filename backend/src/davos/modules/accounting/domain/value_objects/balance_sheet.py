from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from davos.modules.accounting.domain.value_objects.statement_line import StatementLine


@dataclass(frozen=True)
class BalanceSheet:
    as_of: date
    assets: tuple[StatementLine, ...]
    liabilities: tuple[StatementLine, ...]
    equity: tuple[StatementLine, ...]
    current_earnings_irr: int  # profit of the year not yet moved to retained earnings by a year-end closing

    @property
    def total_assets(self) -> int:
        return sum(line.amount_irr for line in self.assets)

    @property
    def total_liabilities(self) -> int:
        return sum(line.amount_irr for line in self.liabilities)

    @property
    def total_equity(self) -> int:
        return sum(line.amount_irr for line in self.equity) + self.current_earnings_irr

    @property
    def difference_irr(self) -> int:
        """Always zero when the books are intact: assets = liabilities + equity."""
        return self.total_assets - self.total_liabilities - self.total_equity
