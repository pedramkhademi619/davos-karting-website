from __future__ import annotations

import hashlib
import hmac
from collections.abc import Sequence
from datetime import datetime

from davos.modules.booking.domain.errors.invalid_webhook_signature_error import InvalidWebhookSignatureError


class WebhookSignatureVerifier:
    """Verifies ``X-Davos-Signature: t=<unix seconds>,v1=<hex hmac-sha256>``.

    The signature covers ``"<t>." + raw body bytes`` (the original payload, never a re-serialised
    one), so a captured request cannot be replayed outside the tolerance window and the timestamp
    cannot be swapped. ``secrets`` may hold the current and previous key to rotate without downtime.
    """

    def __init__(self, *, secrets: Sequence[str], tolerance_seconds: int) -> None:
        self._secrets = [s.encode() for s in secrets if s]
        self._tolerance = tolerance_seconds

    def verify(self, header: str, body: bytes, now: datetime) -> None:
        timestamp, signatures = self._parse(header)
        if abs(now.timestamp() - timestamp) > self._tolerance:
            raise InvalidWebhookSignatureError("timestamp_outside_window")
        signed = f"{timestamp}.".encode() + body
        for secret in self._secrets:
            expected = hmac.new(secret, signed, hashlib.sha256).hexdigest()
            if any(hmac.compare_digest(expected, candidate) for candidate in signatures):
                return
        raise InvalidWebhookSignatureError("signature_mismatch")

    @staticmethod
    def _parse(header: str) -> tuple[int, list[str]]:
        timestamp: int | None = None
        signatures: list[str] = []
        for part in header.split(","):
            key, _, value = part.strip().partition("=")
            if key == "t" and value.isdigit():
                timestamp = int(value)
            elif key == "v1" and value:
                signatures.append(value)
        if timestamp is None or not signatures:
            raise InvalidWebhookSignatureError("malformed_header")
        return timestamp, signatures
