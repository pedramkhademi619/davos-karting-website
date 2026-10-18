from enum import StrEnum


class StatusLevel(StrEnum):
    OK = "ok"
    DEGRADED = "degraded"  # works, but needs attention (slow, backlog, stale job)
    DOWN = "down"
    DISABLED = "disabled"  # switched off on purpose (no key, payments off)
    TEST = "test"  # works in a test/sandbox mode, not for real customers
