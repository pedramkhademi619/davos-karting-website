import uuid

import pytest

from davos.modules.loyalty.application.use_cases.award_points_command import AwardPointsCommand
from davos.modules.loyalty.application.use_cases.award_points_use_case import AwardPointsUseCase
from davos.modules.loyalty.application.use_cases.expire_points_use_case import ExpirePointsUseCase
from davos.modules.loyalty.application.use_cases.get_loyalty_summary_use_case import GetLoyaltySummaryUseCase
from davos.modules.loyalty.application.use_cases.reverse_points_use_case import ReversePointsUseCase
from davos.modules.loyalty.application.use_cases.spend_points_command import SpendPointsCommand
from davos.modules.loyalty.application.use_cases.spend_points_use_case import SpendPointsUseCase
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.errors.insufficient_points_error import InsufficientPointsError
from davos.modules.loyalty.domain.errors.invalid_points_entry_error import InvalidPointsEntryError
from davos.modules.loyalty.domain.services.tier_ladder import TierLadder
from davos.modules.loyalty.domain.value_objects.tier_rule import TierRule
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_points_ledger import InMemoryPointsLedger

ME = uuid.uuid4()
LADDER = TierLadder([TierRule("Regular", 0), TierRule("Silver", 1000), TierRule("Gold", 5000)])


class Harness:
    def __init__(self) -> None:
        self.clock, self.uow, self.ledger = FixedClock(), FakeUnitOfWork(), InMemoryPointsLedger()
        args = {"uow": self.uow, "ledger": self.ledger, "clock": self.clock}
        self.award = AwardPointsUseCase(**args)
        self.spend = SpendPointsUseCase(**args)
        self.reverse = ReversePointsUseCase(**args)
        self.expire = ExpirePointsUseCase(**args)
        self.summary = GetLoyaltySummaryUseCase(ladder=LADDER, **args)

    async def earn(self, points: int, ref: str, days: int | None = None):
        return await self.award.execute(AwardPointsCommand(ME, points, ref, "booking", days))


async def test_award_is_idempotent_per_source_event() -> None:
    h = Harness()
    first = await h.earn(100, "booking-1")
    replay = await h.earn(100, "booking-1")
    assert first.applied and not replay.applied and replay.balance == 100
    assert len(h.ledger.rows) == 1


async def test_spending_reduces_the_balance_and_is_idempotent() -> None:
    h = Harness()
    await h.earn(100, "b1")
    first = await h.spend.execute(SpendPointsCommand(ME, 30, "redeem-1", "discount"))
    replay = await h.spend.execute(SpendPointsCommand(ME, 30, "redeem-1", "discount"))
    assert (first.balance, first.applied) == (70, True)
    assert (replay.balance, replay.applied) == (70, False)


async def test_cannot_spend_more_than_the_balance() -> None:
    h = Harness()
    await h.earn(50, "b1")
    with pytest.raises(InsufficientPointsError):
        await h.spend.execute(SpendPointsCommand(ME, 51, "r1", "x"))
    assert sum(r.delta for r in h.ledger.rows) == 50


@pytest.mark.parametrize("points", [0, -5])
async def test_spend_amount_must_be_positive(points: int) -> None:
    with pytest.raises(InvalidPointsEntryError):
        await Harness().spend.execute(SpendPointsCommand(ME, points, "r", "x"))


async def test_reversal_is_a_compensating_line_and_the_original_stays() -> None:
    h = Harness()
    await h.earn(100, "booking-1")
    result = await h.reverse.execute(
        customer_id=ME, original_kind=PointsEntryKind.EARN, original_source_ref="booking-1", reason="booking cancelled"
    )
    assert result.balance == 0 and len(h.ledger.rows) == 2
    assert h.ledger.rows[0].delta == 100  # never edited
    again = await h.reverse.execute(
        customer_id=ME, original_kind=PointsEntryKind.EARN, original_source_ref="booking-1", reason="booking cancelled"
    )
    assert not again.applied and again.balance == 0  # cancelling twice does not double-refund


async def test_reversing_a_spend_returns_the_points() -> None:
    h = Harness()
    await h.earn(100, "b1")
    await h.spend.execute(SpendPointsCommand(ME, 40, "r1", "x"))
    result = await h.reverse.execute(
        customer_id=ME, original_kind=PointsEntryKind.SPEND, original_source_ref="r1", reason="refund"
    )
    assert result.balance == 100


async def test_reversing_something_that_never_happened_is_not_found() -> None:
    with pytest.raises(NotFoundError):
        await Harness().reverse.execute(
            customer_id=ME, original_kind=PointsEntryKind.EARN, original_source_ref="nope", reason="x"
        )


async def test_expiry_appends_one_line_per_day_and_is_idempotent() -> None:
    h = Harness()
    await h.earn(100, "b1", days=30)
    assert await h.expire.execute(ME) == 0  # not expired yet
    h.clock.advance(days=31)
    assert await h.expire.execute(ME) == 100
    assert await h.expire.execute(ME) == 0
    assert sum(r.delta for r in h.ledger.rows) == 0


async def test_summary_shows_balance_tier_progress_and_expiring_points() -> None:
    h = Harness()
    await h.earn(1200, "b1", days=365)
    await h.earn(300, "b2", days=10)
    await h.spend.execute(SpendPointsCommand(ME, 200, "r1", "x"))
    summary = await h.summary.execute(ME)
    assert summary.balance == 1300 and summary.lifetime_points == 1500
    assert summary.tier_name == "Silver" and summary.next_tier_name == "Gold" and summary.points_to_next_tier == 3500
    assert summary.expiring_soon == 100  # the 300 that expire in 10 days, minus the 200 spent from the oldest
    h.clock.advance(days=1)
    assert (await h.summary.execute(ME)).tier_name == "Silver"  # the tier survives time passing


async def test_a_new_customer_has_a_regular_empty_account() -> None:
    summary = await Harness().summary.execute(uuid.uuid4())
    assert (summary.balance, summary.tier_name, summary.expiring_soon) == (0, "Regular", 0)
