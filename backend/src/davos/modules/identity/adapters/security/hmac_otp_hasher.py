from __future__ import annotations

import hashlib
import hmac

from davos.modules.identity.application.ports.otp_hasher import OtpHasher


class HmacOtpHasher(OtpHasher):
    """HMAC-SHA256 keyed with a server-side secret and bound to the mobile number.

    A leaked database alone cannot be used to recover 6-digit codes offline.
    """

    def __init__(self, secret: str) -> None:
        self._key = secret.encode()

    def digest(self, mobile: str, code: str) -> str:
        return hmac.new(self._key, f"{mobile}:{code}".encode(), hashlib.sha256).hexdigest()
