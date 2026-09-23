from __future__ import annotations

from collections.abc import Sequence

from davos.modules.loyalty.domain.value_objects.tier_rule import TierRule
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class TierLadder:
    """Membership tiers, configurable by administrators (names and thresholds are data, not code)."""

    def __init__(self, rules: Sequence[TierRule]) -> None:
        ordered = sorted(rules, key=lambda r: r.min_lifetime_points)
        if not ordered or ordered[0].min_lifetime_points != 0:
            raise ValidationError("پله اول باشگاه باید از صفر امتیاز شروع شود.", code="invalid_tier_ladder")
        if len({r.min_lifetime_points for r in ordered}) != len(ordered):
            raise ValidationError("آستانه پله‌ها باید یکتا باشد.", code="invalid_tier_ladder")
        self._rules = tuple(ordered)

    def tier_for(self, lifetime_points: int) -> TierRule:
        current = self._rules[0]
        for rule in self._rules:
            if lifetime_points >= rule.min_lifetime_points:
                current = rule
        return current

    def next_tier(self, lifetime_points: int) -> TierRule | None:
        return next((r for r in self._rules if r.min_lifetime_points > lifetime_points), None)
