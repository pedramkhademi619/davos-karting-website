import uuid
from datetime import UTC, datetime, timedelta

from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.services.points_ledger_calculator import PointsLedgerCalculator as Calc

K = PointsEntryKind
NOW = datetime(2026, 6, 1, tzinfo=UTC)
CUSTOMER = uuid.uuid4()


def e(
    kind: PointsEntryKind,
    delta: int,
    ref: str = "x",
    expires: datetime | None = None,
    reverses: PointsEntryKind | None = None,
) -> PointsEntry:
    return PointsEntry(uuid.uuid4(), CUSTOMER, delta, kind, ref, "r", NOW, expires, reverses)


def test_balance_is_the_sum_of_all_lines() -> None:
    assert Calc.balance([e(K.EARN, 100, "a"), e(K.SPEND, -30, "b"), e(K.ADJUST, 5, "c")]) == 75


def test_lifetime_earned_ignores_spending_and_expiry_but_honours_earn_reversals() -> None:
    entries = [
        e(K.EARN, 1000, "a"),
        e(K.SPEND, -400, "b"),
        e(K.EXPIRE, -100, "c"),
        e(K.EARN, 200, "d"),
        e(K.REVERSAL, -200, "rev", reverses=K.EARN),
    ]
    assert Calc.lifetime_earned(entries) == 1000  # spending never demotes a customer; a refunded earn does


def test_a_reversed_spend_returns_points_without_counting_as_new_earning() -> None:
    entries = [e(K.EARN, 500, "a"), e(K.SPEND, -200, "b"), e(K.REVERSAL, 200, "rev", reverses=K.SPEND)]
    assert Calc.balance(entries) == 500 and Calc.lifetime_earned(entries) == 500


def test_expiry_takes_oldest_points_first() -> None:
    past, future = NOW - timedelta(days=1), NOW + timedelta(days=60)
    entries = [e(K.EARN, 100, "old", expires=past), e(K.EARN, 100, "new", expires=future), e(K.SPEND, -40, "s")]
    assert Calc.expirable(entries, NOW) == 60  # 100 old - 40 already spent (spending drains the oldest)


def test_nothing_expires_when_spending_already_consumed_the_expired_points() -> None:
    past = NOW - timedelta(days=1)
    entries = [e(K.EARN, 100, "old", expires=past), e(K.SPEND, -100, "s")]
    assert Calc.expirable(entries, NOW) == 0


def test_expiry_never_exceeds_the_balance_and_is_not_repeated() -> None:
    past = NOW - timedelta(days=1)
    entries = [e(K.EARN, 100, "old", expires=past), e(K.EXPIRE, -100, "expiry:2026-06-01")]
    assert Calc.expirable(entries, NOW) == 0


def test_expiring_soon_counts_only_the_notice_window() -> None:
    entries = [
        e(K.EARN, 100, "soon", expires=NOW + timedelta(days=10)),
        e(K.EARN, 50, "later", expires=NOW + timedelta(days=90)),
    ]
    assert Calc.expiring_within(entries, NOW, NOW + timedelta(days=30)) == 100
