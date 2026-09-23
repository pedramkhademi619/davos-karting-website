from enum import StrEnum


class WebhookOutcome(StrEnum):
    ACCEPTED = "accepted"
    DUPLICATE = "duplicate"
    STALE_IGNORED = "stale_ignored"
