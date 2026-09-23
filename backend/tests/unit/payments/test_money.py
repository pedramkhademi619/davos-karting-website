import pytest

from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money


def test_toman_conversion_is_explicit_and_exact() -> None:
    assert Money.from_toman(1500).irr == 15_000
    assert Money(15_000).to_toman() == 1500
    with pytest.raises(ValidationError):
        Money(15_005).to_toman()  # would silently lose a rial


@pytest.mark.parametrize("bad", [-1, 1.5, "100", True, None])
def test_only_non_negative_integers_are_money(bad: object) -> None:
    with pytest.raises(ValidationError):
        Money(bad)  # type: ignore[arg-type]


def test_percent_uses_integer_floor_rounding() -> None:
    assert Money(999).percent_floor(10).irr == 99
    assert Money(1_000_000).percent_floor(15).irr == 150_000
    with pytest.raises(ValidationError):
        Money(1).percent_floor(101)


def test_subtraction_never_goes_negative() -> None:
    assert Money(100).subtract_floor_zero(Money(500)).irr == 0


def test_cap_and_addition() -> None:
    assert Money(900).capped_at(Money(500)).irr == 500
    assert (Money(1) + Money(2)).irr == 3
