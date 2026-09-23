from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from davos.modules.loyalty.domain.entities.discount_rule import DiscountRule
from davos.modules.loyalty.domain.enums.discount_source import DiscountSource
from davos.modules.loyalty.domain.value_objects.applied_discount import AppliedDiscount
from davos.modules.loyalty.domain.value_objects.price_quote import PriceQuote
from davos.shared_kernel.domain.money import Money

_SOURCE_ORDER = {source: index for index, source in enumerate(DiscountSource)}


class DiscountEngine:
    """Deterministic pricing with explicit stacking.

    Rules:
    1. Only active rules for the service are considered (not revoked, in date range, in scope).
    2. A non-stackable rule never combines with anything. Stackable rules combine only with other
       stackable rules, applied one after another on the remaining price in source order
       (permanent -> tier -> coupon, then rule id).
    3. The customer gets the better of "best single non-stackable rule" and "all stackable rules";
       ties go to the stackable set, then to source order and rule id, so the result never depends
       on the order the rules were supplied in.
    4. Every discount is integer-rounded down, capped by its own cap, and the total can never exceed
       the price (no negative totals).
    """

    def price(self, base: Money, service_id: str, rules: Sequence[DiscountRule], now: datetime) -> PriceQuote:
        active = [r for r in rules if r.is_active(service_id, now)]
        stackable = sorted((r for r in active if r.stackable), key=self._order)
        exclusive = sorted((r for r in active if not r.stackable), key=self._order)

        stacked = self._apply_stack(base, stackable)
        best_single = self._best_single(base, exclusive)

        chosen = stacked
        if best_single and self._total(best_single) > self._total(stacked):
            chosen = best_single
        total_discount = min(self._total(chosen), base.irr)
        return PriceQuote(base=base, discounts=tuple(chosen), total=Money(base.irr - total_discount))

    @staticmethod
    def _order(rule: DiscountRule) -> tuple[int, str]:
        return _SOURCE_ORDER[rule.source], rule.rule_id

    @staticmethod
    def _total(applied: Sequence[AppliedDiscount]) -> int:
        return sum(d.amount.irr for d in applied)

    @staticmethod
    def _apply_stack(base: Money, rules: Sequence[DiscountRule]) -> list[AppliedDiscount]:
        remaining = base
        applied: list[AppliedDiscount] = []
        for rule in rules:
            amount = rule.amount_for(remaining)
            if amount.irr == 0:
                continue
            applied.append(AppliedDiscount(rule.rule_id, rule.source, amount))
            remaining = remaining.subtract_floor_zero(amount)
        return applied

    def _best_single(self, base: Money, rules: Sequence[DiscountRule]) -> list[AppliedDiscount]:
        best: AppliedDiscount | None = None
        for rule in rules:  # already in tie-break order, so the first maximum wins
            amount = rule.amount_for(base)
            if amount.irr > 0 and (best is None or amount.irr > best.amount.irr):
                best = AppliedDiscount(rule.rule_id, rule.source, amount)
        return [best] if best else []
