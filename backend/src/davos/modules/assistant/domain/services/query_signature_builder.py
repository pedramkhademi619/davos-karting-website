from __future__ import annotations

import re

from davos.modules.assistant.domain.value_objects.discriminator_lexicon import CACHE_DISTINCTIONS, CHANNEL_SYNONYMS
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

_NUMBER = re.compile(r"\d+")


class QuerySignatureBuilder:
    """Reduces a question to the details that decide its answer: every number and every discriminator word.

    Two questions may share a stored answer only if their signatures are equal, however close their embeddings are:
    "Friday" and "Saturday", "single-seater" and "two-seater", "book online" and "book by phone" are almost the same
    to an embedding model and have different answers. The word list is not complete (no list can be), which is why the
    similarity threshold is also high and both are checked against pairs of look-alike questions
    (``evals/assistant/cache_pairs.jsonl``).
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def build(self, text: str) -> str:
        normalized = self._normalizer.normalize(text)
        numbers = sorted({str(int(match)) for match in _NUMBER.findall(normalized)})
        canonical = (CHANNEL_SYNONYMS.get(token, token) for token in normalized.split())
        words = sorted({token for token in canonical if token in CACHE_DISTINCTIONS})
        if not numbers and not words:
            return ""
        return f"n:{','.join(numbers)}|w:{','.join(words)}"
