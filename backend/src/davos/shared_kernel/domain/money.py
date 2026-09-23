from __future__ import annotations

from dataclasses import dataclass

from davos.shared_kernel.domain.errors.validation_error import ValidationError

_RIAL_PER_TOMAN = 10


@dataclass(frozen=True, order=True)
class Money:
    """Non-negative amount stored as integer Iranian Rial (IRR). Floats are never used."""

    irr: int

    def __post_init__(self) -> None:
        if isinstance(self.irr, bool) or not isinstance(self.irr, int):
            raise ValidationError("مبلغ باید عدد صحیح باشد.", code="money_not_integer")
        if self.irr < 0:
            raise ValidationError("مبلغ نمی‌تواند منفی باشد.", code="money_negative")

    @classmethod
    def zero(cls) -> Money:
        return cls(0)

    @classmethod
    def from_toman(cls, toman: int) -> Money:
        return cls(toman * _RIAL_PER_TOMAN)

    def to_toman(self) -> int:
        """Explicit display conversion; fails instead of silently dropping a Rial digit."""
        if self.irr % _RIAL_PER_TOMAN:
            raise ValidationError("مبلغ بر حسب تومان عدد صحیح نیست.", code="money_not_whole_toman")
        return self.irr // _RIAL_PER_TOMAN

    def __add__(self, other: Money) -> Money:
        return Money(self.irr + other.irr)

    def subtract_floor_zero(self, other: Money) -> Money:
        """Subtraction that can never produce a negative total."""
        return Money(max(self.irr - other.irr, 0))

    def percent_floor(self, percent: int) -> Money:
        """``percent`` % of this amount, rounded down using integer arithmetic only."""
        if not 0 <= percent <= 100:
            raise ValidationError("درصد باید بین ۰ تا ۱۰۰ باشد.", code="percent_out_of_range")
        return Money(self.irr * percent // 100)

    def capped_at(self, cap: Money) -> Money:
        return Money(min(self.irr, cap.irr))
