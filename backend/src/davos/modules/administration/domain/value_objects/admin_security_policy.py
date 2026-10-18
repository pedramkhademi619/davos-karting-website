from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class AdminSecurityPolicy:
    """Brute-force and idle-session limits for staff sign-in. Values come from the settings (ADMIN_*)."""

    max_failed_logins: int  # wrong passwords in a row before the account is locked
    lockout: timedelta
    idle_timeout: timedelta  # a session unused for this long ends
    logins_per_ip_per_15_minutes: int
