from __future__ import annotations

import hashlib
import secrets

from davos.modules.administration.application.ports.admin_token_service import AdminTokenService


class Sha256AdminTokenService(AdminTokenService):
    def new_token(self) -> str:
        return secrets.token_urlsafe(32)

    def digest(self, raw: str) -> str:
        return hashlib.sha256(("admin:" + raw).encode()).hexdigest()
