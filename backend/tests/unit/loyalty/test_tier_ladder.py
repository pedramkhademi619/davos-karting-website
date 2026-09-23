import pytest

from davos.modules.loyalty.domain.services.tier_ladder import TierLadder
from davos.modules.loyalty.domain.value_objects.tier_rule import TierRule
from davos.shared_kernel.domain.errors.validation_error import ValidationError

LADDER = TierLadder([TierRule("Gold", 5000), TierRule("Regular", 0), TierRule("Silver", 1000), TierRule("VIP", 10000)])


@pytest.mark.parametrize(
    ("points", "tier"),
    [
        (0, "Regular"),
        (999, "Regular"),
        (1000, "Silver"),
        (4999, "Silver"),
        (5000, "Gold"),
        (9999, "Gold"),
        (10000, "VIP"),
        (10**9, "VIP"),
    ],
)
def test_tier_boundaries_are_inclusive_and_order_independent(points: int, tier: str) -> None:
    assert LADDER.tier_for(points).name == tier


def test_next_tier() -> None:
    assert LADDER.next_tier(0).name == "Silver"  # type: ignore[union-attr]
    assert LADDER.next_tier(10000) is None


def test_ladder_must_start_at_zero_and_have_unique_thresholds() -> None:
    with pytest.raises(ValidationError):
        TierLadder([TierRule("Silver", 100)])
    with pytest.raises(ValidationError):
        TierLadder([TierRule("A", 0), TierRule("B", 100), TierRule("C", 100)])
    with pytest.raises(ValidationError):
        TierLadder([])
