from dataclasses import dataclass

from davos.modules.loyalty.domain.enums.discount_source import DiscountSource
from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class AppliedDiscount:
    rule_id: str
    source: DiscountSource
    amount: Money
