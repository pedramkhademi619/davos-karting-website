"""Helpers that play the role of the booking system when signing and building webhooks."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from datetime import UTC, datetime, timedelta

SECRET = "b" * 40
BASE_TIME = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def sign(body: bytes, *, secret: str = SECRET, timestamp: int) -> str:
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def payload(
    user_id: uuid.UUID,
    *,
    event_id: str = "evt-1",
    booking: str = "bk-1",
    status: str = "confirmed",
    updated_minutes: int = 0,
    amount: int = 500_000,
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "external_booking_id": booking,
        "user_id": str(user_id),
        "status": status,
        "amount_irr": amount,
        "session_time": (BASE_TIME + timedelta(days=3)).isoformat(),
        "updated_at": (BASE_TIME + timedelta(minutes=updated_minutes)).isoformat(),
    }


def encode(data: dict[str, object]) -> bytes:
    return json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode()
