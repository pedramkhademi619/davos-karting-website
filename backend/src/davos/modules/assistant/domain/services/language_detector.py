from __future__ import annotations

from davos.modules.assistant.domain.enums.language import Language

# Letters and digits that exist only in the Persian or only in the Arabic way of writing.
_PERSIAN_MARKS = frozenset("پچژگکی۰۱۲۳۴۵۶۷۸۹")
_ARABIC_MARKS = frozenset("يكةىأإؤ٠١٢٣٤٥٦٧٨٩")


class LanguageDetector:
    """Tells Persian, Arabic and English apart by their script. The site is Persian, so doubt resolves to Persian."""

    def detect(self, text: str) -> Language:
        latin = sum(1 for c in text if "a" <= c.lower() <= "z")
        arabic_script = sum(1 for c in text if "؀" <= c <= "ۿ")
        if latin > arabic_script:
            return Language.ENGLISH
        persian = sum(1 for c in text if c in _PERSIAN_MARKS)
        arabic = sum(1 for c in text if c in _ARABIC_MARKS)
        return Language.ARABIC if arabic > persian else Language.PERSIAN
