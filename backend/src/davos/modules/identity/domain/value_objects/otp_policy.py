from dataclasses import dataclass


@dataclass(frozen=True)
class OtpPolicy:
    code_length: int = 6
    ttl_seconds: int = 120
    max_attempts: int = 3
    resend_cooldown_seconds: int = 60
