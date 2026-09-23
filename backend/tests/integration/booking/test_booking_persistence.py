import asyncio
import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.booking.application.services.webhook_outcome import WebhookOutcome
from davos.modules.booking.domain.errors.booking_owner_mismatch_error import BookingOwnerMismatchError
from tests.support.booking_webhooks import encode, payload, sign

pytestmark = pytest.mark.integration
USER = uuid.uuid4()


async def deliver(container: ApplicationContainer, data: dict[str, object]) -> WebhookOutcome:
    body = encode(data)
    header = sign(body, timestamp=int(container.clock.now().timestamp()))
    return await container.process_booking_webhook().execute(raw_body=body, signature_header=header)


async def count(engine: AsyncEngine, sql: str) -> int:
    async with engine.connect() as conn:
        return int((await conn.execute(text(sql))).scalar_one())


async def test_the_same_webhook_delivered_concurrently_is_applied_once(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    outcomes = await asyncio.gather(*(deliver(container, payload(USER)) for _ in range(12)))
    assert outcomes.count(WebhookOutcome.ACCEPTED) == 1
    assert outcomes.count(WebhookOutcome.DUPLICATE) == 11
    assert await count(engine, "SELECT count(*) FROM booking_records") == 1
    assert await count(engine, "SELECT count(*) FROM outbox_messages WHERE event_name = 'booking.BookingVerified'") == 1
    assert await count(engine, "SELECT count(*) FROM booking_webhook_inbox WHERE status = 'processed'") == 1


async def test_out_of_order_events_leave_the_newest_state_in_the_database(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await deliver(container, payload(USER, event_id="e3", status="attended", updated_minutes=30))
    stale = await deliver(container, payload(USER, event_id="e1", status="confirmed", updated_minutes=0))
    assert stale is WebhookOutcome.STALE_IGNORED
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT status FROM booking_records"))).scalar_one() == "attended"
        assert (
            await conn.execute(text("SELECT count(*) FROM outbox_messages"))
        ).scalar_one() == 1  # no event for the stale one


async def test_concurrent_events_for_one_booking_serialise_and_keep_the_newest(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await deliver(container, payload(USER, event_id="e0", status="pending", updated_minutes=0))
    events = [
        payload(USER, event_id=f"e{i}", status=s, updated_minutes=i)
        for i, s in enumerate(["confirmed", "cancelled", "confirmed", "attended", "no_show", "refunded"], start=1)
    ]
    await asyncio.gather(*(deliver(container, e) for e in events))
    async with engine.connect() as conn:
        assert (
            await conn.execute(text("SELECT status FROM booking_records"))
        ).scalar_one() == "refunded"  # updated_at is highest


async def test_a_failed_event_survives_a_rollback_and_can_be_reprocessed(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await deliver(container, payload(USER))
    with pytest.raises(BookingOwnerMismatchError):
        await deliver(container, payload(uuid.uuid4(), event_id="e2", updated_minutes=5))
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text("SELECT status, attempts, last_error_code FROM booking_webhook_inbox WHERE event_id = 'e2'")
            )
        ).one()
    assert (row.status, row.attempts, row.last_error_code) == ("failed", 1, "booking_owner_mismatch")

    recovered, failing = await container.reprocess_failed_booking_webhooks().execute()
    assert (recovered, failing) == (0, 1)  # still wrong data: it stays parked, visible to operators
    async with engine.connect() as conn:
        assert (
            await conn.execute(text("SELECT attempts FROM booking_webhook_inbox WHERE event_id = 'e2'"))
        ).scalar_one() == 2


async def test_the_return_status_reads_only_verified_owned_records(container: ApplicationContainer) -> None:
    pending = await container.booking_return_status().execute(external_booking_id="bk-1", user_id=USER)
    assert pending.state == "pending_confirmation"
    await deliver(container, payload(USER))
    assert (
        await container.booking_return_status().execute(external_booking_id="bk-1", user_id=USER)
    ).state == "confirmed"
    other = await container.booking_return_status().execute(external_booking_id="bk-1", user_id=uuid.uuid4())
    assert other.state == "pending_confirmation"


@pytest.mark.parametrize(("column", "value"), [("amount_irr", -1), ("status", "vip")])
async def test_database_constraints_reject_impossible_bookings(engine: AsyncEngine, column: str, value: object) -> None:
    values = {"amount_irr": 1, "status": "confirmed", column: value}
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    "INSERT INTO booking_records (id, external_booking_id, user_id, status, amount_irr, "
                    "session_time, last_updated_at, last_event_id, created_at) "
                    "VALUES (gen_random_uuid(), 'x', gen_random_uuid(), :status, :amount_irr, now(), now(), 'e', now())"
                ),
                values,
            )


async def test_external_booking_ids_are_unique(engine: AsyncEngine) -> None:
    insert = text(
        "INSERT INTO booking_records (id, external_booking_id, user_id, status, amount_irr, session_time, "
        "last_updated_at, last_event_id, created_at) "
        "VALUES (gen_random_uuid(), 'same', gen_random_uuid(), 'pending', 1, now(), now(), 'e', now())"
    )
    async with engine.begin() as conn:
        await conn.execute(insert)
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(insert)
