from __future__ import annotations

import logging
import re

_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Kavenegar puts the API key in the URL path; HTTP client logs print request URLs.
    (re.compile(r"(?i)(api\.kavenegar\.com/v1/)[^/\s]+"), r"\1[redacted]"),
    (re.compile(r"(?<!\d)(?:\+98|0098|98|0)9\d{9}(?!\d)"), "[mobile]"),
    (re.compile(r"(?i)bearer\s+[a-z0-9._\-]+"), "Bearer [redacted]"),
    (re.compile(r"(?i)\b(sk|key|token|secret)[-_][a-z0-9]{8,}"), "[redacted-key]"),
    (
        re.compile(r"(?i)(otp|code|password|api_key|authorization|token|secret|authority)\s*[=:]\s*\S+"),
        r"\1=[redacted]",
    ),
)


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class SensitiveDataFilter(logging.Filter):
    """Last line of defence: masks phone numbers, tokens and OTP-like values in log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        return True
