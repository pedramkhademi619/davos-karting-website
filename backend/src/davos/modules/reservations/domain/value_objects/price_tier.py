from __future__ import annotations

from dataclasses import dataclass

from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class PriceTier:
    """Price of one kart for one session. A two-seater is priced per kart, not per person."""

    single: Money
    double: Money

    def total(self, single_count: int, double_count: int) -> Money:
        return Money(self.single.irr * single_count + self.double.irr * double_count)
