from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.value_objects.sales_summary_day import SalesSummaryDay


@dataclass(frozen=True)
class SalesSummary:
    days: tuple[SalesSummaryDay, ...]

    @property
    def online_irr(self) -> int:
        return sum(d.online_irr for d in self.days)

    @property
    def cash_irr(self) -> int:
        return sum(d.cash_irr for d in self.days)

    @property
    def card_irr(self) -> int:
        return sum(d.card_irr for d in self.days)

    @property
    def transfer_irr(self) -> int:
        return sum(d.transfer_irr for d in self.days)

    @property
    def revenue_irr(self) -> int:
        return sum(d.revenue_irr for d in self.days)

    @property
    def received_irr(self) -> int:
        return self.online_irr + self.cash_irr + self.card_irr + self.transfer_irr
