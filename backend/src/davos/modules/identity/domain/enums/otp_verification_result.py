from enum import StrEnum


class OtpVerificationResult(StrEnum):
    VERIFIED = "verified"
    WRONG_CODE = "wrong_code"
    EXPIRED = "expired"
    LOCKED = "locked"
    ALREADY_USED = "already_used"
    SUPERSEDED = "superseded"
