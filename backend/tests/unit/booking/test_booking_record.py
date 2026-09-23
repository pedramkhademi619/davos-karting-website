import uuid

import pytest

from davos.modules.booking.domain.entities.booking_record import BookingRecord
from davos.modules.booking.domain.enums.apply_result import ApplyResult
from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.modules.booking.domain.errors.booking_owner_mismatch_error import BookingOwnerMismatchError
from davos.modules.booking.domain.events.booking_status_changed import BookingStatusChanged
from davos.modules.booking.domain.events.booking_verified import BookingVerified
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from tests.support.booking_webhooks import BASE_TIME, encode, payload

USER = uuid.uuid4()
parse = BookingEventParser().parse


def event(**kw):
    return parse(encode(payload(USER, **kw)))


def test_the_first_event_creates_the_record_and_announces_a_verified_booking() -> None:
    record = BookingRecord.from_event(event(), BASE_TIME)
    events = record.pull_events()
    assert isinstance(events[0], BookingVerified) and events[0].external_booking_id == "bk-1"
    assert record.status is BookingStatus.CONFIRMED


def test_a_newer_event_updates_and_announces_the_status_change() -> None:
    record = BookingRecord.from_event(event(), BASE_TIME)
    record.pull_events()
    assert record.apply(event(event_id="e2", status="cancelled", updated_minutes=5), BASE_TIME) is ApplyResult.APPLIED
    change = record.pull_events()[0]
    assert isinstance(change, BookingStatusChanged) and (change.previous_status, change.status) == (
        "confirmed",
        "cancelled",
    )


@pytest.mark.parametrize("minutes", [0, -5])
def test_equal_or_older_events_are_ignored_without_side_effects(minutes: int) -> None:
    record = BookingRecord.from_event(event(updated_minutes=10), BASE_TIME)
    record.pull_events()
    assert (
        record.apply(event(event_id="late", status="cancelled", updated_minutes=10 + minutes), BASE_TIME)
        is ApplyResult.STALE_IGNORED
    )
    assert record.status is BookingStatus.CONFIRMED and record.pull_events() == []


def test_a_newer_event_with_the_same_status_updates_details_without_a_status_event() -> None:
    record = BookingRecord.from_event(event(), BASE_TIME)
    record.pull_events()
    record.apply(event(event_id="e2", amount=600_000, updated_minutes=1), BASE_TIME)
    assert record.amount.irr == 600_000 and record.pull_events() == []


def test_an_event_for_a_different_customer_is_refused() -> None:
    record = BookingRecord.from_event(event(), BASE_TIME)
    other = parse(encode(payload(uuid.uuid4(), event_id="e2", updated_minutes=1)))
    with pytest.raises(BookingOwnerMismatchError):
        record.apply(other, BASE_TIME)
    assert record.user_id == USER
