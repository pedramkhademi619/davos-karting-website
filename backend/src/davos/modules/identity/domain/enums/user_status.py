from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "active"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
