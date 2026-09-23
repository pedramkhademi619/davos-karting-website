from __future__ import annotations

import hashlib
import hmac


class CsrfTokenService:
    """Stateless CSRF token: an HMAC of the session token with a dedicated secret.

    The SPA reads it from a non-HttpOnly cookie or response body and echoes it in the
    ``X-CSRF-Token`` header; an attacker on another origin can neither read nor forge it.
    """

    def __init__(self, secret: str) -> None:
        self._key = secret.encode()

    def token_for(self, raw_session_token: str) -> str:
        return hmac.new(self._key, raw_session_token.encode(), hashlib.sha256).hexdigest()

    def is_valid(self, raw_session_token: str, presented: str) -> bool:
        if not raw_session_token or not presented:
            return False
        return hmac.compare_digest(self.token_for(raw_session_token), presented)
