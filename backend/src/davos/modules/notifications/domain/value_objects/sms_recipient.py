from __future__ import annotations

import re
from dataclasses import dataclass

from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer
from davos.shared_kernel.domain.errors.validation_error import ValidationError

_SEPARATORS = re.compile(r"[\s\-().‌‏‎]")
_NATIONAL = re.compile(r"9\d{9}")


@dataclass(frozen=True)
class SmsRecipient:
    """An Iranian mobile number in the 09xxxxxxxxx form SMS providers expect."""

    local: str

    @classmethod
    def parse(cls, raw: str) -> SmsRecipient:
        cleaned = _SEPARATORS.sub("", DigitNormalizer.to_ascii(raw))
        national = cleaned
        for prefix in ("+98", "0098", "98", "0"):
            if cleaned.startswith(prefix):
                national = cleaned[len(prefix) :]
                break
        if not _NATIONAL.fullmatch(national):
            raise ValidationError(f"شماره موبایل معتبر نیست: {raw[:20]}", code="invalid_mobile")
        return cls(f"0{national}")

    def masked(self) -> str:
        return f"{self.local[:4]}***{self.local[-4:]}"
