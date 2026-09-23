from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from davos.modules.loyalty.domain.enums.discount_source import DiscountSource
from davos.modules.loyalty.domain.enums.discount_value_type import DiscountValueType
from davos.modules.loyalty.domain.errors.invalid_discount_rule_error import InvalidDiscountRuleError
from davos.shared_kernel.domain.money import Money


@dataclass(frozen=True)
class DiscountRule:
    """A discount a customer may be entitled to (permanent grant, tier benefit or coupon).

    ``stackable`` is opt-in: a rule that is not stackable can never be combined with another one.
    An empty ``service_ids`` set means the rule applies to every service.
    """

    rule_id: str
    source: DiscountSource
    value_type: DiscountValueType
    value: int
    stackable: bool = False
    cap: Money | None = None
    service_ids: frozenset[str] = field(default_factory=frozenset)
    valid_from: datetime | None = None
    valid_until: datetime | None = None  # None = permanent
    revoked: bool = False

    def __post_init__(self) -> None:
        if self.value <= 0:
            raise InvalidDiscountRuleError("مقدار تخفیف باید مثبت باشد.")
        if self.value_type is DiscountValueType.PERCENT and self.value > 100:
            raise InvalidDiscountRuleError("درصد تخفیف نمی‌تواند بیشتر از ۱۰۰ باشد.")
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise InvalidDiscountRuleError("بازه اعتبار تخفیف معتبر نیست.")

    def is_active(self, service_id: str, now: datetime) -> bool:
        if self.revoked:
            return False
        if self.service_ids and service_id not in self.service_ids:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        return not (self.valid_until and now >= self.valid_until)

    def amount_for(self, price: Money) -> Money:
        """Discount this rule gives on ``price``: integer arithmetic, capped, never above the price."""
        raw = price.percent_floor(self.value) if self.value_type is DiscountValueType.PERCENT else Money(self.value)
        if self.cap is not None:
            raw = raw.capped_at(self.cap)
        return raw.capped_at(price)
