import asyncio
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.loyalty.application.use_cases.award_points_command import AwardPointsCommand
from davos.modules.loyalty.application.use_cases.spend_points_command import SpendPointsCommand
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind
from davos.modules.loyalty.domain.errors.insufficient_points_error import InsufficientPointsError

pytestmark = pytest.mark.integration


async def balance(engine: AsyncEngine, customer: uuid.UUID) -> int:
    async with engine.connect() as conn:
        return int(
            (
                await conn.execute(
                    text("SELECT COALESCE(SUM(delta), 0) FROM loyalty_points_ledger WHERE customer_id = :c"),
                    {"c": customer},
                )
            ).scalar_one()
        )


async def test_the_same_verified_event_processed_many_times_grants_points_once(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    customer = uuid.uuid4()
    results = await asyncio.gather(
        *(
            container.award_points().execute(AwardPointsCommand(customer, 100, "booking-42", "booking"))
            for _ in range(12)
        )
    )
    assert sum(r.applied for r in results) == 1
    assert await balance(engine, customer) == 100


async def test_concurrent_redemptions_never_spend_more_than_the_balance(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    customer = uuid.uuid4()
    await container.award_points().execute(AwardPointsCommand(customer, 100, "seed", "seed"))

    async def redeem(i: int) -> bool:
        try:
            result = await container.spend_points().execute(SpendPointsCommand(customer, 10, f"redeem-{i}", "discount"))
        except InsufficientPointsError:
            return False
        return result.applied

    outcomes = await asyncio.gather(*(redeem(i) for i in range(30)))
    assert sum(outcomes) == 10  # exactly balance/10 redemptions succeeded
    assert await balance(engine, customer) == 0  # and the balance never went negative


async def test_the_same_redemption_replayed_concurrently_spends_once(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    customer = uuid.uuid4()
    await container.award_points().execute(AwardPointsCommand(customer, 100, "seed", "seed"))
    results = await asyncio.gather(
        *(container.spend_points().execute(SpendPointsCommand(customer, 40, "redeem-x", "d")) for _ in range(8))
    )
    assert sum(r.applied for r in results) == 1
    assert await balance(engine, customer) == 60


async def test_reversal_and_expiry_are_new_lines_never_edits(
    container: ApplicationContainer, engine: AsyncEngine, clock
) -> None:
    customer = uuid.uuid4()
    await container.award_points().execute(
        AwardPointsCommand(customer, 100, "booking-1", "booking", expires_in_days=30)
    )
    await container.reverse_points().execute(
        customer_id=customer, original_kind=PointsEntryKind.EARN, original_source_ref="booking-1", reason="cancelled"
    )
    async with engine.connect() as conn:
        rows = (
            await conn.execute(text("SELECT kind, delta FROM loyalty_points_ledger ORDER BY created_at, kind"))
        ).all()
    assert sorted((r.kind, r.delta) for r in rows) == [("earn", 100), ("reversal", -100)]
    assert await balance(engine, customer) == 0


async def test_the_database_makes_the_ledger_append_only(container: ApplicationContainer, engine: AsyncEngine) -> None:
    customer = uuid.uuid4()
    await container.award_points().execute(AwardPointsCommand(customer, 100, "booking-1", "booking"))
    async with engine.connect() as conn:
        with pytest.raises(DBAPIError, match="append-only"):
            await conn.execute(text("UPDATE loyalty_points_ledger SET delta = 999999"))
    async with engine.connect() as conn:
        with pytest.raises(DBAPIError, match="append-only"):
            await conn.execute(text("DELETE FROM loyalty_points_ledger"))
    assert await balance(engine, customer) == 100


@pytest.mark.parametrize(("kind", "delta"), [("earn", -5), ("spend", 5), ("expire", 1), ("earn", 0), ("bonus", 5)])
async def test_database_constraints_reject_impossible_ledger_lines(engine: AsyncEngine, kind: str, delta: int) -> None:
    customer = uuid.uuid4()
    async with engine.begin() as conn:
        await conn.execute(
            text("INSERT INTO loyalty_accounts (customer_id, created_at) VALUES (:c, now())"), {"c": customer}
        )
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    "INSERT INTO loyalty_points_ledger (id, customer_id, delta, kind, source_ref, reason, created_at) "
                    "VALUES (gen_random_uuid(), :c, :d, :k, 'x', 'r', now())"
                ),
                {"c": customer, "d": delta, "k": kind},
            )
