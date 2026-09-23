from __future__ import annotations

import re
from collections.abc import Iterable

from davos.modules.assistant.domain.value_objects.discriminator_lexicon import DISCRIMINATOR_WORDS
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

_NUMBER = re.compile(r"\d+")


class QuerySignatureBuilder:
    """Reduces a question to the details that decide its answer: every number and every discriminator word.

    Two questions may share a cached answer only if their signatures are equal, however similar their embeddings are
    ("12 years old, 140 cm" and "12 years old, 135 cm" are close in embedding space and have different answers).
    Extra words (a new vehicle, a new kind of day) can be added from settings without touching the code.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None, extra_words: Iterable[str] = ()) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()
        extra = {self._normalizer.normalize(word) for word in extra_words}
        self._words = DISCRIMINATOR_WORDS | frozenset(word for word in extra if word)

    def build(self, text: str) -> str:
        normalized = self._normalizer.normalize(text)
        numbers = sorted({str(int(match)) for match in _NUMBER.findall(normalized)})
        words = sorted({token for token in normalized.split() if token in self._words})
        if not numbers and not words:
            return ""
        return f"n:{','.join(numbers)}|w:{','.join(words)}"
