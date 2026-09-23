from enum import StrEnum


class VerificationOutcome(StrEnum):
    VERIFIED = "verified"
    ALREADY_VERIFIED = "already_verified"
    REJECTED = "rejected"
