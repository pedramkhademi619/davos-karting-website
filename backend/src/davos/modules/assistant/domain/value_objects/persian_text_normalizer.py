from __future__ import annotations

import re
import unicodedata

_CHAR_MAP = str.maketrans(
    {
        "ي": "ی",  # Arabic yeh
        "ى": "ی",  # alef maqsura
        "ك": "ک",  # Arabic kaf
        "ة": "ه",  # teh marbuta
        "ۀ": "ه",  # heh with yeh above
        "ؤ": "و",
        "أ": "ا",
        "إ": "ا",
        "ٱ": "ا",
        "‌": " ",  # ZWNJ (half-space) -> space so 'می خواهم' and 'می‌خواهم' match
        "‍": None,  # ZWJ
        "‎": None,  # LRM
        "‏": None,  # RLM
        "ـ": None,  # tatweel
    }
)
_DIGITS = str.maketrans(
    {**{ord(c): str(i) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹")}, **{ord(c): str(i) for i, c in enumerate("٠١٢٣٤٥٦٧٨٩")}}
)
_DIACRITICS = re.compile("[ً-ٰٟۖ-ۭ]")
_NON_WORD = re.compile(r"[^\w]+|_+")
_SPACES = re.compile(r"\s+")


class PersianTextNormalizer:
    """Canonical form used for both indexing and querying Persian text.

    Handles Arabic/Persian letter variants (ي/ی, ك/ک), ZWNJ, diacritics, tatweel, digit
    scripts (۱۲۳ / ١٢٣ -> 123) and punctuation, so 'یا' typed with either keyboard finds
    the same entry.
    """

    def normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.translate(_CHAR_MAP).translate(_DIGITS)
        text = _DIACRITICS.sub("", text)
        text = _NON_WORD.sub(" ", text.casefold())
        return _SPACES.sub(" ", text).strip()
