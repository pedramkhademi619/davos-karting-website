from dataclasses import dataclass


@dataclass(frozen=True)
class OtpRateLimitPolicy:
    """Limits on requesting and trying codes. The limits come from the settings (OTP_*_PER_*); the windows are part of
    those settings' names (per hour, per 15 minutes)."""

    per_mobile_limit: int
    per_ip_limit: int
    verify_per_ip_limit: int
    per_mobile_window_seconds: int = 3600
    per_ip_window_seconds: int = 3600
    verify_per_ip_window_seconds: int = 900
