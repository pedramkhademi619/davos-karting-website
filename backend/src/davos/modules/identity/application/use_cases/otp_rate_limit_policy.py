from dataclasses import dataclass


@dataclass(frozen=True)
class OtpRateLimitPolicy:
    per_mobile_limit: int = 5
    per_mobile_window_seconds: int = 3600
    per_ip_limit: int = 20
    per_ip_window_seconds: int = 3600
    verify_per_ip_limit: int = 30
    verify_per_ip_window_seconds: int = 900
