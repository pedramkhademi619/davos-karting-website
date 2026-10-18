from __future__ import annotations

import re

from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer

_LETTERS = str.maketrans({"ي": "ی", "ك": "ک", "أ": "ا", "إ": "ا", "ة": "ه", "ۀ": "ه"})
_INVISIBLE = re.compile("[‌‍‎‏ـً-ٰٟ]")  # ZWNJ, marks, kashida, diacritics
_THOUSANDS = re.compile(r"(?<=\d)[,٬،](?=\d{3}(?!\d))")
_MILLIONS = re.compile(r"(\d+|یک)\s*میلیون(?:\s*و\s*(\d+)\s*هزار)?")
_THOUSAND_WORD = re.compile(r"(\d+)\s*هزار")


class GradingText:
    """Makes replies comparable with the expected facts: one digit set, one letter set, no invisible characters,
    thousands separators removed and spelled amounts turned into numbers ("۷ میلیون و ۱۱۰ هزار" -> "7110000",
    "۷۹۰ هزار" -> "790000"), lower case for the English replies."""

    @staticmethod
    def normalize(text: str) -> str:
        value = DigitNormalizer.to_ascii(text).translate(_LETTERS)
        value = _INVISIBLE.sub("", value)
        value = _THOUSANDS.sub("", value)
        value = _MILLIONS.sub(GradingText._millions, value)
        value = _THOUSAND_WORD.sub(lambda m: str(int(m.group(1)) * 1000), value)
        return re.sub(r"\s+", " ", value).strip().lower()

    @staticmethod
    def _millions(match: re.Match[str]) -> str:
        millions = 1 if match.group(1) == "یک" else int(match.group(1))
        thousands = int(match.group(2) or 0)
        return str(millions * 1_000_000 + thousands * 1000)
