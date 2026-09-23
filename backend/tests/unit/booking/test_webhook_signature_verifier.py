import json

import pytest

from davos.modules.booking.domain.errors.invalid_webhook_signature_error import InvalidWebhookSignatureError
from davos.modules.booking.domain.services.webhook_signature_verifier import WebhookSignatureVerifier
from tests.support.booking_webhooks import BASE_TIME, SECRET, sign

NOW = BASE_TIME
TS = int(NOW.timestamp())
BODY = b'{"event_id":"e1","status":"confirmed"}'
verifier = WebhookSignatureVerifier(secrets=[SECRET], tolerance_seconds=300)


def reason_of(header: str, body: bytes = BODY, at=NOW) -> str:
    with pytest.raises(InvalidWebhookSignatureError) as info:
        verifier.verify(header, body, at)
    return info.value.reason


def test_a_correct_signature_is_accepted() -> None:
    verifier.verify(sign(BODY, timestamp=TS), BODY, NOW)


def test_a_tampered_body_is_rejected() -> None:
    assert reason_of(sign(BODY, timestamp=TS), BODY.replace(b"confirmed", b"refunded")) == "signature_mismatch"


def test_the_signature_covers_the_original_bytes_not_a_reserialised_payload() -> None:
    reordered = json.dumps(json.loads(BODY), sort_keys=True, indent=1).encode()
    assert reason_of(sign(BODY, timestamp=TS), reordered) == "signature_mismatch"


def test_a_wrong_key_is_rejected() -> None:
    assert reason_of(sign(BODY, secret="x" * 40, timestamp=TS)) == "signature_mismatch"


def test_swapping_the_timestamp_invalidates_the_signature() -> None:
    header = sign(BODY, timestamp=TS - 10)
    forged = header.replace(f"t={TS - 10}", f"t={TS}")
    assert reason_of(forged) == "signature_mismatch"


@pytest.mark.parametrize("delta", [-301, 301, -86400, 3600])
def test_requests_outside_the_validity_window_are_rejected_even_if_correctly_signed(delta: int) -> None:
    assert reason_of(sign(BODY, timestamp=TS + delta)) == "timestamp_outside_window"


@pytest.mark.parametrize("delta", [-300, 0, 300])
def test_the_window_boundaries_are_inclusive(delta: int) -> None:
    verifier.verify(sign(BODY, timestamp=TS + delta), BODY, NOW)


@pytest.mark.parametrize(
    "header", ["", "garbage", "t=abc,v1=ff", f"t={TS}", f"v1={'a' * 64}", f"t=,v1={'a' * 64}", "t=1,v1="]
)
def test_malformed_headers_are_rejected(header: str) -> None:
    assert reason_of(header) == "malformed_header"


def test_a_previous_key_still_works_during_rotation_and_multiple_signatures_are_supported() -> None:
    rotating = WebhookSignatureVerifier(secrets=["n" * 40, SECRET], tolerance_seconds=300)
    rotating.verify(sign(BODY, timestamp=TS), BODY, NOW)  # signed with the old key
    both = sign(BODY, secret="z" * 40, timestamp=TS) + "," + sign(BODY, timestamp=TS).split(",", 1)[1]
    rotating.verify(both, BODY, NOW)


def test_no_configured_key_means_nothing_verifies() -> None:
    with pytest.raises(InvalidWebhookSignatureError):
        WebhookSignatureVerifier(secrets=[""], tolerance_seconds=300).verify(sign(BODY, timestamp=TS), BODY, NOW)


def test_error_message_is_generic() -> None:
    with pytest.raises(InvalidWebhookSignatureError) as info:
        verifier.verify("garbage", BODY, NOW)
    assert "signature_mismatch" not in info.value.message and info.value.code == "webhook_signature_invalid"
