from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SalesSummaryDay:
    day: date
    online_irr: int  # paid on the website
    cash_irr: int  # paid at the counter in cash (into the till)
    card_irr: int  # paid at the counter by card reader or card-to-card transfer (into the bank)
    revenue_irr: int  # revenue earned that day (differs from receipts when tickets are booked ahead)

    @property
    def received_irr(self) -> int:
        return self.online_irr + self.cash_irr + self.card_irr
