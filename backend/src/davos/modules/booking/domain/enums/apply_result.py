from enum import StrEnum


class ApplyResult(StrEnum):
    APPLIED = "applied"
    STALE_IGNORED = "stale_ignored"
