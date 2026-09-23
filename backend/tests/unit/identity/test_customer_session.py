from datetime import UTC, datetime, timedelta

import pytest

from davos.modules.identity.domain.entities.customer_session import CustomerSession
from davos.modules.identity.domain.services.ip_anonymizer import IpAnonymizer

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def _session() -> CustomerSession:
    import uuid

    return CustomerSession.start(
        user_id=uuid.uuid4(),
        token_digest="d",
        user_agent="UA" * 300,
        client_ip="203.0.113.77",
        now=NOW,
        lifetime=timedelta(days=30),
    )


def test_session_lifecycle() -> None:
    session = _session()
    assert session.is_active(NOW)
    assert not session.is_active(NOW + timedelta(days=30))
    session.revoke(NOW)
    assert not session.is_active(NOW)


def test_user_agent_is_truncated_and_ip_is_anonymised() -> None:
    session = _session()
    assert len(session.user_agent) == 200
    assert session.ip_hint == "203.0.113.0/24"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2001:db8:abcd:1234::1", "2001:db8:abcd::/48"), ("garbage", ""), ("", "")],
)
def test_anonymize_ip(raw: str, expected: str) -> None:
    assert IpAnonymizer.anonymize(raw) == expected


def test_touch_is_throttled() -> None:
    session = _session()
    assert session.touch(NOW + timedelta(minutes=1)) is False
    assert session.touch(NOW + timedelta(minutes=6)) is True
