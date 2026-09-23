from __future__ import annotations

import re
from dataclasses import dataclass

from davos.modules.identity.domain.errors.invalid_mobile_number_error import InvalidMobileNumberError
from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer

_SEPARATORS = re.compile(r"[\s\-().‌‏‎]")
_IRAN_MOBILE = re.compile(r"9\d{9}")


@dataclass(frozen=True)
class MobileNumber:
    """Canonical Iranian mobile number in E.164 form: +989XXXXXXXXX."""

    e164: str

    @classmethod
    def parse(cls, raw: str) -> MobileNumber:
        cleaned = _SEPARATORS.sub("", DigitNormalizer.to_ascii(raw))
        national = cleaned
        for prefix in ("+98", "0098", "98", "0"):
            if cleaned.startswith(prefix):
                national = cleaned[len(prefix) :]
                break
        if not _IRAN_MOBILE.fullmatch(national):
            raise InvalidMobileNumberError
        return cls(f"+98{national}")

    @property
    def local(self) -> str:
        """09XXXXXXXXX form, as expected by most Iranian SMS providers."""
        return f"0{self.e164[3:]}"

    def masked(self) -> str:
        """Safe representation for logs and audit trails."""
        return f"{self.e164[:6]}***{self.e164[-4:]}"

    def __str__(self) -> str:
        return self.e164
