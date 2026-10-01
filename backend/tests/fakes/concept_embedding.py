"""A stand-in for the embedding model, for tests that need no 129 MB model: a question's "meaning" is the set of
concepts its words mention, so any two questions about the same concept are identical to it (like a real model,
which cannot tell "Friday" from "Saturday" apart reliably), and questions about different concepts are unrelated."""

from __future__ import annotations

import math

from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding

# Written the way PersianTextNormalizer leaves text (no half-spaces, no punctuation).
CONCEPTS: tuple[tuple[str, ...], ...] = (
    ("قیمت", "هزینه", "نرخ", "تعرفه"),
    ("ساعت کار", "بازید", "باز هستید"),
    ("رزرو", "نوبت"),
    ("باشگاه",),
    ("پرداخت", "درگاه"),
)


class ConceptEmbedding(EmbeddingPort):
    def __init__(self, *, ready: bool = True, fail: bool = False) -> None:
        self.ready = ready
        self.fail = fail
        self.warm_ups = 0
        self.embedded: list[str] = []

    @property
    def model_name(self) -> str:
        return "concept-test-embedding"

    async def warm_up(self) -> None:
        self.warm_ups += 1

    async def embed_query(self, text: str) -> QueryEmbedding:
        if not self.ready or self.fail:
            raise EmbeddingUnavailableError("the test embedding is switched off")
        self.embedded.append(text)
        hits = [1.0 if any(word in text for word in group) else 0.0 for group in CONCEPTS]
        vector = [*hits, 1.0 if not any(hits) else 0.0]  # the last dimension: about none of the known concepts
        norm = math.sqrt(sum(v * v for v in vector))
        return QueryEmbedding(tuple(v / norm for v in vector))
