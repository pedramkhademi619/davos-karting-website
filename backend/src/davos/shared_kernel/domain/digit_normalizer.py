from __future__ import annotations

_PERSIAN = "۰۱۲۳۴۵۶۷۸۹"
_ARABIC_INDIC = "٠١٢٣٤٥٦٧٨٩"
_TABLE = {ord(c): str(i) for i, c in enumerate(_PERSIAN)} | {ord(c): str(i) for i, c in enumerate(_ARABIC_INDIC)}


class DigitNormalizer:
    """Persian (۰-۹) and Arabic-Indic (٠-٩) digits to ASCII."""

    @staticmethod
    def to_ascii(text: str) -> str:
        return text.translate(_TABLE)
