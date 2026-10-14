from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VatReport:
    collected_irr: int  # VAT charged on sales
    paid_irr: int  # VAT paid on purchases and expenses
    opening_balance_irr: int  # owed (positive) or recoverable (negative) before the period

    @property
    def net_payable_irr(self) -> int:
        """What is owed to the tax authority at the end of the period (negative when it owes the business)."""
        return self.opening_balance_irr + self.collected_irr - self.paid_irr
