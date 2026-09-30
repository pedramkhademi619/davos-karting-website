from __future__ import annotations

from dataclasses import dataclass

from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class ReservationQuote:
    amount: Money
    description: str
