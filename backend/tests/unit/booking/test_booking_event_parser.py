import uuid

import pytest

from davos.modules.booking.domain.enums.booking_status import BookingStatus
from davos.modules.booking.domain.errors.invalid_booking_event_error import InvalidBookingEventError
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from tests.support.booking_webhooks import encode, payload

parser = BookingEventParser()
USER = uuid.uuid4()


def test_a_valid_payload_becomes_a_typed_event() -> None:
    event = parser.parse(encode(payload(USER)))
    assert event.event_id == "evt-1" and event.user_id == USER and event.status is BookingStatus.CONFIRMED
    assert event.amount.irr == 500_000 and event.session_time.tzinfo is not None


@pytest.mark.parametrize(
    "field", ["event_id", "external_booking_id", "user_id", "status", "amount_irr", "session_time", "updated_at"]
)
def test_every_field_is_required(field: str) -> None:
    data = payload(USER)
    del data[field]
    with pytest.raises(InvalidBookingEventError):
        parser.parse(encode(data))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount_irr", 12.5),
        ("amount_irr", "500"),
        ("amount_irr", True),
        ("amount_irr", -1),
        ("status", "vip"),
        ("status", 5),
        ("user_id", "not-a-uuid"),
        ("event_id", ""),
        ("event_id", "x" * 101),
        ("session_time", "2026-01-04T12:00:00"),
        ("updated_at", "yesterday"),
        ("external_booking_id", None),
    ],
)
def test_invalid_values_are_rejected(field: str, value: object) -> None:
    data = payload(USER)
    data[field] = value
    with pytest.raises(InvalidBookingEventError):
        parser.parse(encode(data))


@pytest.mark.parametrize("body", [b"", b"not json", b"[]", b"null", b'"text"', b"\xff\xfe"])
def test_non_object_or_broken_json_is_rejected(body: bytes) -> None:
    with pytest.raises(InvalidBookingEventError):
        parser.parse(body)
