from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from davos.modules.loyalty.domain.value_objects.applied_discount import AppliedDiscount
from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class PriceQuote:
    base: Money
    discounts: tuple[AppliedDiscount, ...]
    total: Money

    @property
    def total_discount(self) -> Money:
        return Money(self.base.irr - self.total.irr)

    def snapshot(self) -> dict[str, Any]:
        """Immutable record of the rules that produced this price, stored with the booking or payment."""
        return {
            "base_irr": self.base.irr,
            "total_irr": self.total.irr,
            "applied": [
                {"rule_id": d.rule_id, "source": d.source.value, "amount_irr": d.amount.irr} for d in self.discounts
            ],
        }
