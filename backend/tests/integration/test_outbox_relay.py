from __future__ import annotations

import asyncio
import uuid
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.composition.application_container import ApplicationContainer
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.platform.messaging.outbox_dispatcher import OutboxDispatcher
from davos.platform.messaging.outbox_envelope import OutboxEnvelope
from davos.platform.messaging.outbox_relay import OutboxRelay

pytestmark = pytest.mark.integration


class RecordingDispatcher(OutboxDispatcher):
    def __init__(self, *, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.delivered: list[OutboxEnvelope] = []

    async def dispatch(self, envelope: OutboxEnvelope) -> None:
        if self.fail_times > 0:
            self.fail_times -= 1
            raise ConnectionError("broker is down for 09123456789")
        self.delivered.append(envelope)


async def _publish_events(container: ApplicationContainer, count: int) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    uow = container.new_unit_of_work()
    async with uow:
        for i in range(count):
            user = User.register(mobile=MobileNumber.parse(f"0912000{i:04d}"), now=container.clock.now())
            events = user.pull_events()
            ids.extend(e.event_id for e in events)
            uow.collect_events(events)
        await uow.commit()
    return ids


def relay(container: ApplicationContainer, dispatcher: OutboxDispatcher, **kwargs) -> OutboxRelay:
    return OutboxRelay(
        session_factory=container.session_factory,
        dispatcher=dispatcher,
        clock=container.clock,
        jitter=lambda: 1.0,
        **kwargs,
    )


async def test_committed_events_are_dispatched_once_and_marked_published(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    ids = await _publish_events(container, 3)
    dispatcher = RecordingDispatcher()

    report = await relay(container, dispatcher).run_once()

    assert report.dispatched == 3 and report.failed == 0
    assert {e.event_id for e in dispatcher.delivered} == set(ids)
    assert all(e.event_name == "identity.UserRegistered" for e in dispatcher.delivered)
    again = await relay(container, dispatcher).run_once()
    assert again.dispatched == 0  # already published: not sent twice
    async with engine.connect() as conn:
        assert (
            await conn.execute(text("SELECT count(*) FROM outbox_messages WHERE published_at IS NULL"))
        ).scalar_one() == 0


async def test_failures_back_off_exponentially_then_recover(
    container: ApplicationContainer, engine: AsyncEngine, clock
) -> None:
    await _publish_events(container, 1)
    dispatcher = RecordingDispatcher(fail_times=2)
    r = relay(container, dispatcher, base_backoff_seconds=10)

    assert (await r.run_once()).failed == 1
    assert (await r.run_once()).dispatched == 0  # not yet due: backoff has not elapsed
    clock.advance(seconds=11)
    assert (await r.run_once()).failed == 1  # second failure
    clock.advance(seconds=15)
    assert (await r.run_once()).dispatched == 0  # second backoff is 20s, only 15s elapsed
    clock.advance(seconds=6)
    assert (await r.run_once()).dispatched == 1  # recovered

    async with engine.connect() as conn:
        row = (await conn.execute(text("SELECT attempts, last_error FROM outbox_messages"))).one()
    assert row.attempts == 2


async def test_error_details_that_may_contain_personal_data_are_not_stored(
    container: ApplicationContainer, engine: AsyncEngine
) -> None:
    await _publish_events(container, 1)
    await relay(container, RecordingDispatcher(fail_times=1)).run_once()
    async with engine.connect() as conn:
        last_error = (await conn.execute(text("SELECT last_error FROM outbox_messages"))).scalar_one()
    assert last_error == "ConnectionError" and "0912" not in last_error


async def test_events_that_keep_failing_are_dead_lettered_not_retried_forever(
    container: ApplicationContainer, engine: AsyncEngine, clock
) -> None:
    await _publish_events(container, 1)
    r = relay(container, RecordingDispatcher(fail_times=99), max_attempts=3, base_backoff_seconds=1)
    reports = []
    for _ in range(4):
        reports.append(await r.run_once())
        clock.advance(seconds=60)
    assert sum(x.dead_lettered for x in reports) == 1
    async with engine.connect() as conn:
        row = (await conn.execute(text("SELECT dead_lettered_at, published_at, attempts FROM outbox_messages"))).one()
    assert row.dead_lettered_at is not None and row.published_at is None and row.attempts == 3


async def test_concurrent_relays_never_dispatch_the_same_event_twice(container: ApplicationContainer) -> None:
    await _publish_events(container, 20)
    dispatcher = RecordingDispatcher()
    reports = await asyncio.gather(*(relay(container, dispatcher, batch_size=5).run_once() for _ in range(6)))
    ids = [e.event_id for e in dispatcher.delivered]
    assert len(ids) == len(set(ids)) == sum(r.dispatched for r in reports)
    await relay(container, dispatcher, batch_size=50).run_once()
    assert len({e.event_id for e in dispatcher.delivered}) == 20  # everything is delivered eventually


async def test_backoff_is_capped_and_jittered(container: ApplicationContainer) -> None:
    low = OutboxRelay(
        session_factory=container.session_factory,
        dispatcher=RecordingDispatcher(),
        clock=container.clock,
        jitter=lambda: 0.0,
        base_backoff_seconds=10,
    )
    high = OutboxRelay(
        session_factory=container.session_factory,
        dispatcher=RecordingDispatcher(),
        clock=container.clock,
        jitter=lambda: 1.0,
        base_backoff_seconds=10,
    )
    assert low._backoff(1) == timedelta(seconds=5) and high._backoff(1) == timedelta(seconds=10)
    assert high._backoff(30) == timedelta(seconds=3600)
