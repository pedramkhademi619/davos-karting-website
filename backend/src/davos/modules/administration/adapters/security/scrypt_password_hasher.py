from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from davos.modules.administration.application.ports.password_hasher import PasswordHasher

_N, _R, _P = 2**15, 8, 1  # about 32 MiB and a few tens of milliseconds per check
_MAXMEM = 64 * 1024 * 1024
_KEY_LENGTH = 32


class ScryptPasswordHasher(PasswordHasher):
    """scrypt (memory-hard, standard library). Format: ``scrypt$N$r$p$salt$hash`` with base64 salt and hash."""

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = self._derive(password, salt, _N, _R, _P)
        return "$".join(("scrypt", str(_N), str(_R), str(_P), self._b64(salt), self._b64(digest)))

    def verify(self, password: str, stored: str) -> bool:
        try:
            scheme, n, r, p, salt, expected = stored.split("$")
            if scheme != "scrypt":
                return False
            actual = self._derive(password, base64.b64decode(salt), int(n), int(r), int(p))
            return hmac.compare_digest(actual, base64.b64decode(expected))
        except (ValueError, TypeError):
            return False

    def dummy_verify(self, password: str) -> None:
        self._derive(password, b"davos-dummy-salt", _N, _R, _P)

    @staticmethod
    def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, maxmem=_MAXMEM, dklen=_KEY_LENGTH)

    @staticmethod
    def _b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode("ascii")
