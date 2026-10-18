from dataclasses import dataclass


@dataclass(frozen=True)
class OtpPolicy:
    """How one-time codes behave. Values come from the settings (OTP_*), built in the composition root."""

    code_length: int
    ttl_seconds: int
    max_attempts: int
    resend_cooldown_seconds: int
