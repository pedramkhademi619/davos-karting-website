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


# A question containing this word is "a little off" its concept: similar to the other questions about it (0.86), but not
# identical, which is where the language model's check decides.
BLUR_WORD = "احتمالا"


class ConceptEmbedding(EmbeddingPort):
    def __init__(self, *, ready: bool = True, fail: bool = False, dimensions: int = 0) -> None:
        self.dimensions = dimensions  # pad with zeros to this size (the database column is 384); 0 = as is
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
        other = (
            1.0 if not any(hits) else (0.6 if BLUR_WORD in text else 0.0)
        )  # the last dimension: none of the concepts
        vector = [*hits, other]
        norm = math.sqrt(sum(v * v for v in vector))
        unit = [v / norm for v in vector]
        return QueryEmbedding(tuple(unit + [0.0] * max(0, self.dimensions - len(unit))))
