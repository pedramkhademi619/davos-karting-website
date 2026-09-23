from __future__ import annotations

import hashlib
import secrets

from davos.modules.identity.application.ports.issued_token import IssuedToken
from davos.modules.identity.application.ports.session_token_service import SessionTokenService


class Sha256SessionTokenService(SessionTokenService):
    """256-bit random bearer tokens; only their SHA-256 digest is persisted.

    The token is high-entropy, so a fast unsalted hash is appropriate (unlike passwords).
    """

    def issue(self) -> IssuedToken:
        raw = secrets.token_urlsafe(32)
        return IssuedToken(raw=raw, digest=self.digest(raw))

    def digest(self, raw: str) -> str:
        return hashlib.sha256(raw.encode()).hexdigest()
