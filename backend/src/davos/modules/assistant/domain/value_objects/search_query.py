from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.persian_stopwords import PERSIAN_STOPWORDS
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer


@dataclass(frozen=True)
class SearchQuery:
    original: str
    normalized: str
    tokens: tuple[str, ...]

    @classmethod
    def from_text(cls, text: str, normalizer: PersianTextNormalizer) -> SearchQuery:
        normalized = normalizer.normalize(text)
        words = normalized.split()
        meaningful = tuple(w for w in words if w not in PERSIAN_STOPWORDS) or tuple(words)
        return cls(original=text, normalized=normalized, tokens=meaningful)

    @property
    def match_text(self) -> str:
        """Text sent to the search backend: stop-words removed, single-spaced."""
        return " ".join(self.tokens)

    @property
    def is_empty(self) -> bool:
        return not self.tokens
