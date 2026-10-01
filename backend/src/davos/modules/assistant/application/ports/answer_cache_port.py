from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


class AnswerCachePort(ABC):
    """Stored answers, kept until someone retires them: an answer is not served once the texts it was made from have
    changed (its fingerprint no longer matches), but it is never deleted for being old."""

    @abstractmethod
    async def find_candidates(
        self, embedding: QueryEmbedding, *, embedding_model: str, fingerprint: str, limit: int
    ) -> list[CacheCandidate]:
        """The nearest active entries (most similar first) made by the same embedding model under the same
        fingerprint."""

    @abstractmethod
    async def store(self, entry: NewCacheEntry) -> None: ...

    @abstractmethod
    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        """Counts one more use of the entry and remembers when it was last served."""

    @abstractmethod
    async def deactivate(self, entry_id: uuid.UUID) -> None:
        """Stops serving the entry (a customer found its answer not helpful, or a person retired it)."""
