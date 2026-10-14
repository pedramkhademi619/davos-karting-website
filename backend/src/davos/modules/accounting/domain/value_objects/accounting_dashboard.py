from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.value_objects.monthly_point import MonthlyPoint
from davos.modules.accounting.domain.value_objects.statement_line import StatementLine


@dataclass(frozen=True)
class AccountingDashboard:
    cash_irr: int
    bank_irr: int
    pos_irr: int
    gateway_irr: int
    payables_irr: int
    refunds_payable_irr: int
    vat_balance_irr: int
    today_revenue_irr: int
    month_revenue_irr: int
    month_expenses_irr: int
    unrecognized_advances_irr: int
    trend: tuple[MonthlyPoint, ...]
    top_expenses: tuple[StatementLine, ...]

    @property
    def month_profit_irr(self) -> int:
        return self.month_revenue_irr - self.month_expenses_irr

    @property
    def liquid_irr(self) -> int:
        return self.cash_irr + self.bank_irr + self.pos_irr + self.gateway_irr
