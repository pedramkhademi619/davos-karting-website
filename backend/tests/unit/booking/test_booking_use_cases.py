from __future__ import annotations

import uuid

import pytest

from davos.modules.booking.application.services.booking_event_processor import BookingEventProcessor
from davos.modules.booking.application.services.webhook_outcome import WebhookOutcome
from davos.modules.booking.application.use_cases.get_booking_return_status_use_case import GetBookingReturnStatusUseCase
from davos.modules.booking.application.use_cases.process_booking_webhook_use_case import ProcessBookingWebhookUseCase
from davos.modules.booking.application.use_cases.reprocess_failed_webhooks_use_case import (
    ReprocessFailedWebhooksUseCase,
)
from davos.modules.booking.domain.errors.booking_integration_disabled_error import BookingIntegrationDisabledError
from davos.modules.booking.domain.errors.booking_owner_mismatch_error import BookingOwnerMismatchError
from davos.modules.booking.domain.errors.invalid_booking_event_error import InvalidBookingEventError
from davos.modules.booking.domain.errors.invalid_webhook_signature_error import InvalidWebhookSignatureError
from davos.modules.booking.domain.events.booking_status_changed import BookingStatusChanged
from davos.modules.booking.domain.events.booking_verified import BookingVerified
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from davos.modules.booking.domain.services.webhook_signature_verifier import WebhookSignatureVerifier
from tests.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.in_memory_booking_record_repository import InMemoryBookingRecordRepository
from tests.fakes.in_memory_webhook_inbox import InMemoryWebhookInbox
from tests.support.booking_webhooks import BASE_TIME, SECRET, encode, payload, sign

USER = uuid.uuid4()


class Harness:
    def __init__(self, *, enabled: bool = True) -> None:
        self.clock = FixedClock(BASE_TIME)
        self.uow, self.inbox, self.records = FakeUnitOfWork(), InMemoryWebhookInbox(), InMemoryBookingRecordRepository()
        parser = BookingEventParser()
        self.processor = BookingEventProcessor(uow=self.uow, inbox=self.inbox, records=self.records, clock=self.clock)
        self.webhook = ProcessBookingWebhookUseCase(
            enabled=enabled,
            verifier=WebhookSignatureVerifier(secrets=[SECRET], tolerance_seconds=300),
            parser=parser,
            processor=self.processor,
            clock=self.clock,
        )
        self.reprocess = ReprocessFailedWebhooksUseCase(
            uow=self.uow, inbox=self.inbox, parser=parser, processor=self.processor
        )
        self.return_status = GetBookingReturnStatusUseCase(enabled=enabled, uow=self.uow, records=self.records)

    async def deliver(self, data: dict[str, object], *, signed: bool = True, at_offset: int = 0):
        body = encode(data)
        header = sign(body, timestamp=int(self.clock.now().timestamp()) + at_offset) if signed else "t=1,v1=00"
        return await self.webhook.execute(raw_body=body, signature_header=header)


async def test_disabled_integration_rejects_everything_before_looking_at_the_payload() -> None:
    h = Harness(enabled=False)
    with pytest.raises(BookingIntegrationDisabledError):
        await h.deliver(payload(USER))
    with pytest.raises(BookingIntegrationDisabledError):
        await h.return_status.execute(external_booking_id="bk-1", user_id=USER)
    assert h.inbox.rows == {}


async def test_unsigned_or_forged_deliveries_change_nothing() -> None:
    h = Harness()
    with pytest.raises(InvalidWebhookSignatureError):
        await h.deliver(payload(USER), signed=False)
    with pytest.raises(InvalidWebhookSignatureError):
        await h.deliver(payload(USER), at_offset=-3600)  # correctly signed but replayed from an hour ago
    assert h.records.items == {} and h.inbox.rows == {} and h.uow.commits == 0


async def test_signed_but_malformed_events_are_rejected_without_storage() -> None:
    h = Harness()
    with pytest.raises(InvalidBookingEventError):
        await h.deliver({**payload(USER), "amount_irr": "lots"})
    assert h.records.items == {}


async def test_a_verified_event_creates_the_booking_and_publishes_one_domain_event() -> None:
    h = Harness()
    assert await h.deliver(payload(USER)) is WebhookOutcome.ACCEPTED
    assert h.records.items["bk-1"].user_id == USER
    assert [type(e) for e in h.uow.published_events] == [BookingVerified]


async def test_duplicate_deliveries_are_recognised_and_change_nothing() -> None:
    h = Harness()
    await h.deliver(payload(USER))
    for _ in range(3):
        assert await h.deliver(payload(USER)) is WebhookOutcome.DUPLICATE
    assert len(h.uow.published_events) == 1


async def test_out_of_order_delivery_ends_in_the_newest_state() -> None:
    h = Harness()
    assert (
        await h.deliver(payload(USER, event_id="e-cancel", status="cancelled", updated_minutes=10))
        is WebhookOutcome.ACCEPTED
    )
    late = await h.deliver(payload(USER, event_id="e-confirm", status="confirmed", updated_minutes=5))
    assert late is WebhookOutcome.STALE_IGNORED
    assert h.records.items["bk-1"].status.value == "cancelled"
    assert h.inbox.rows["e-confirm"]["status"] == "processed"  # recorded, so its own redelivery is a duplicate


async def test_a_later_status_change_emits_a_change_event() -> None:
    h = Harness()
    await h.deliver(payload(USER))
    await h.deliver(payload(USER, event_id="e2", status="attended", updated_minutes=60))
    assert isinstance(h.uow.published_events[-1], BookingStatusChanged)


async def test_a_processing_failure_is_stored_for_reprocessing_and_recovers() -> None:
    h = Harness()
    h.records.fail_next_add = True
    with pytest.raises(ConnectionError):
        await h.deliver(payload(USER))
    assert h.inbox.rows["evt-1"]["status"] == "failed" and h.inbox.rows["evt-1"]["error"] == "processing_error"
    assert h.records.items == {}

    recovered, failing = await h.reprocess.execute()
    assert (recovered, failing) == (1, 0)
    assert h.records.items["bk-1"].user_id == USER and h.inbox.rows["evt-1"]["status"] == "processed"
    assert await h.deliver(payload(USER)) is WebhookOutcome.DUPLICATE  # the provider retry is now harmless


async def test_an_event_naming_another_customer_is_parked_as_failed_and_never_applied() -> None:
    h = Harness()
    await h.deliver(payload(USER))
    with pytest.raises(BookingOwnerMismatchError):
        await h.deliver(payload(uuid.uuid4(), event_id="e2", updated_minutes=5))
    assert h.records.items["bk-1"].user_id == USER
    assert h.inbox.rows["e2"]["error"] == "booking_owner_mismatch"


async def test_the_return_page_says_pending_until_our_own_verified_data_exists() -> None:
    h = Harness()
    before = await h.return_status.execute(external_booking_id="bk-1", user_id=USER)
    assert before.state == "pending_confirmation" and before.amount_irr is None
    await h.deliver(payload(USER))
    after = await h.return_status.execute(external_booking_id="bk-1", user_id=USER)
    assert after.state == "confirmed" and after.amount_irr == 500_000


async def test_a_forged_or_foreign_return_never_shows_success() -> None:
    h = Harness()
    await h.deliver(payload(USER))
    stranger = await h.return_status.execute(external_booking_id="bk-1", user_id=uuid.uuid4())
    guessed = await h.return_status.execute(external_booking_id="bk-999", user_id=USER)
    assert stranger.state == guessed.state == "pending_confirmation"
    assert stranger.amount_irr is None and stranger.session_time is None
