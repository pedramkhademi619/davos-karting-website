from __future__ import annotations

import hashlib
import math

from davos.modules.assistant.application.ports.embedding_port import EmbeddingPort
from davos.modules.assistant.application.ports.embedding_unavailable_error import EmbeddingUnavailableError
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


class HashingEmbedding(EmbeddingPort):
    """A deterministic stand-in for the real model: a bag of hashed words, scaled to unit length.

    Identical texts give identical vectors and texts that share most words give a high cosine similarity, which is all
    the pipeline tests need. (The real model is exercised separately, wherever it is installed.)
    """

    def __init__(self, *, dimension: int = 64, model_name: str = "hashing-test") -> None:
        self._dimension = dimension
        self._model_name = model_name
        self.calls: list[str] = []
        self.available = True

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    async def warm_up(self) -> None:
        return None

    async def embed_query(self, text: str) -> QueryEmbedding:
        self.calls.append(text)
        if not self.available:
            raise EmbeddingUnavailableError("the test embedding is switched off")
        values = [0.0] * self._dimension
        for word in text.split():
            values[int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % self._dimension] += 1.0
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return QueryEmbedding(values=tuple(v / norm for v in values), model=self._model_name)
