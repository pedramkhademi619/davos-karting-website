from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SalesSummaryDay:
    day: date
    online_irr: int  # paid through the gateway
    cash_irr: int
    card_irr: int
    transfer_irr: int
    revenue_irr: int  # revenue earned that day (differs from receipts when tickets are booked ahead)

    @property
    def received_irr(self) -> int:
        return self.online_irr + self.cash_irr + self.card_irr + self.transfer_irr
