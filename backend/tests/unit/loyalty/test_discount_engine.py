from datetime import UTC, datetime, timedelta

import pytest

from davos.modules.loyalty.domain.entities.discount_rule import DiscountRule
from davos.modules.loyalty.domain.enums.discount_source import DiscountSource as Src
from davos.modules.loyalty.domain.enums.discount_value_type import DiscountValueType as Kind
from davos.modules.loyalty.domain.errors.invalid_discount_rule_error import InvalidDiscountRuleError
from davos.modules.loyalty.domain.services.discount_engine import DiscountEngine
from davos.shared_kernel.domain.money import Money

NOW = datetime(2026, 6, 1, tzinfo=UTC)
ENGINE = DiscountEngine()
PRICE = Money(1_000_000)


def rule(rule_id: str, source: Src, value: int, kind: Kind = Kind.PERCENT, **kw: object) -> DiscountRule:
    return DiscountRule(rule_id, source, kind, value, **kw)  # type: ignore[arg-type]


def price(rules: list[DiscountRule], base: Money = PRICE, service: str = "kart-15") -> tuple[int, list[str]]:
    quote = ENGINE.price(base, service, rules, NOW)
    return quote.total.irr, [d.rule_id for d in quote.discounts]


def test_no_rules_means_no_discount() -> None:
    assert price([]) == (1_000_000, [])


def test_percentage_and_fixed_discounts() -> None:
    assert price([rule("p", Src.COUPON, 10)]) == (900_000, ["p"])
    assert price([rule("f", Src.COUPON, 50_000, Kind.FIXED)]) == (950_000, ["f"])


def test_percentages_round_down_in_integer_arithmetic() -> None:
    assert price([rule("p", Src.COUPON, 10)], Money(999))[0] == 900  # 99 off, never 99.9


def test_non_stackable_rules_never_combine_the_best_one_wins() -> None:
    total, applied = price([rule("perm", Src.PERMANENT_CUSTOMER, 10), rule("coupon", Src.COUPON, 20)])
    assert (total, applied) == (800_000, ["coupon"])


def test_stackable_rules_combine_sequentially_on_the_remaining_price() -> None:
    total, applied = price(
        [rule("perm", Src.PERMANENT_CUSTOMER, 10, stackable=True), rule("coupon", Src.COUPON, 10, stackable=True)]
    )
    assert total == 810_000  # 10% then 10% of the remainder, not 20%
    assert applied == ["perm", "coupon"]


def test_a_stackable_rule_does_not_combine_with_a_non_stackable_one() -> None:
    total, applied = price([rule("tier", Src.TIER, 5, stackable=True), rule("big", Src.COUPON, 30)])
    assert (total, applied) == (700_000, ["big"])  # best of: stack(5%) vs single(30%)


def test_the_stackable_set_can_beat_a_single_exclusive_rule() -> None:
    total, applied = price(
        [
            rule("a", Src.PERMANENT_CUSTOMER, 15, stackable=True),
            rule("b", Src.TIER, 15, stackable=True),
            rule("c", Src.COUPON, 20),
        ]
    )
    assert total == 722_500 and applied == ["a", "b"]


def test_result_does_not_depend_on_the_order_rules_are_supplied() -> None:
    rules = [
        rule("z", Src.COUPON, 10, stackable=True),
        rule("a", Src.PERMANENT_CUSTOMER, 10, stackable=True),
        rule("m", Src.TIER, 7, stackable=True),
    ]
    forward, backward = price(rules), price(list(reversed(rules)))
    assert forward == backward and forward[1] == ["a", "m", "z"]


def test_ties_prefer_the_higher_precedence_source_deterministically() -> None:
    total, applied = price([rule("coupon", Src.COUPON, 10), rule("perm", Src.PERMANENT_CUSTOMER, 10)])
    assert applied == ["perm"] and total == 900_000


def test_caps_limit_each_discount() -> None:
    capped = rule("c", Src.COUPON, 50, cap=Money(100_000))
    assert price([capped]) == (900_000, ["c"])


def test_a_fixed_discount_can_never_make_the_total_negative() -> None:
    assert price([rule("huge", Src.COUPON, 5_000_000, Kind.FIXED)], Money(300_000)) == (0, ["huge"])


def test_stacked_discounts_can_never_exceed_the_price() -> None:
    total, _ = price(
        [rule("a", Src.PERMANENT_CUSTOMER, 100, stackable=True), rule("b", Src.COUPON, 50, Kind.FIXED, stackable=True)]
    )
    assert total == 0


def test_permanent_and_date_limited_validity() -> None:
    forever = rule("perm", Src.PERMANENT_CUSTOMER, 10)
    expired = rule("old", Src.COUPON, 50, valid_until=NOW - timedelta(days=1))
    future = rule("new", Src.COUPON, 50, valid_from=NOW + timedelta(days=1))
    current = rule("now", Src.COUPON, 20, valid_from=NOW - timedelta(days=1), valid_until=NOW + timedelta(days=1))
    assert price([forever, expired, future]) == (900_000, ["perm"])
    assert price([forever, current]) == (800_000, ["now"])
    assert (
        ENGINE.price(PRICE, "x", [forever], NOW + timedelta(days=3650)).total.irr == 900_000
    )  # still valid in ten years


def test_validity_end_is_exclusive() -> None:
    boundary = rule("b", Src.COUPON, 10, valid_until=NOW)
    assert price([boundary]) == (1_000_000, [])


def test_revoked_rules_are_ignored() -> None:
    assert price([rule("r", Src.PERMANENT_CUSTOMER, 90, revoked=True)]) == (1_000_000, [])


def test_scope_limits_a_rule_to_specific_services() -> None:
    scoped = rule("s", Src.COUPON, 20, service_ids=frozenset({"kart-30"}))
    assert price([scoped], service="kart-15") == (1_000_000, [])
    assert price([scoped], service="kart-30") == (800_000, ["s"])


def test_snapshot_records_exactly_what_was_applied() -> None:
    quote = ENGINE.price(PRICE, "kart-15", [rule("perm", Src.PERMANENT_CUSTOMER, 10)], NOW)
    assert quote.snapshot() == {
        "base_irr": 1_000_000,
        "total_irr": 900_000,
        "applied": [{"rule_id": "perm", "source": "permanent_customer", "amount_irr": 100_000}],
    }
    assert quote.total_discount.irr == 100_000


@pytest.mark.parametrize("kwargs", [{"value": 0}, {"value": -1}, {"value": 101}])
def test_invalid_rules_are_rejected(kwargs: dict) -> None:
    with pytest.raises(InvalidDiscountRuleError):
        DiscountRule("x", Src.COUPON, Kind.PERCENT, **kwargs)


def test_inverted_validity_window_is_rejected() -> None:
    with pytest.raises(InvalidDiscountRuleError):
        rule("x", Src.COUPON, 10, valid_from=NOW, valid_until=NOW - timedelta(days=1))
