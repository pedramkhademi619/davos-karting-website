from dataclasses import dataclass

from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class OrderQuote:
    amount: Money
    description: str
