from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from davos.modules.administration.application.use_cases.authenticated_admin import AuthenticatedAdmin


@dataclass(frozen=True)
class AdminLoginResult:
    token: str
    expires_at: datetime
    admin: AuthenticatedAdmin
