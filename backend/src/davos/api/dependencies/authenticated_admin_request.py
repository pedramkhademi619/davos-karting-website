from __future__ import annotations

from dataclasses import dataclass

from davos.modules.administration.application.use_cases.authenticated_admin import AuthenticatedAdmin


@dataclass(frozen=True)
class AuthenticatedAdminRequest:
    admin: AuthenticatedAdmin
    csrf_token: str
