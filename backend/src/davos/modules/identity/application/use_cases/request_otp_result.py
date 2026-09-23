from dataclasses import dataclass


@dataclass(frozen=True)
class RequestOtpResult:
    expires_in_seconds: int
    resend_after_seconds: int
