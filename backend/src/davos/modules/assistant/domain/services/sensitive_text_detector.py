from __future__ import annotations

import re

_DIGIT = "0-9۰-۹٠-٩"  # Latin, Persian and Arabic-Indic digits
_PHONE_OR_ID = re.compile(rf"(?:[{_DIGIT}][ \-]?){{9,}}")  # mobile numbers, card numbers, national ids
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


class SensitiveTextDetector:
    """Flags text that looks like personal data (a phone or card number, an e-mail address).

    The answer cache keeps question text in its table, so such questions are neither looked up nor stored.
    """

    def contains_sensitive(self, text: str) -> bool:
        return bool(_PHONE_OR_ID.search(text) or _EMAIL.search(text))
