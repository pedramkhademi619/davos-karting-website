from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


class SemanticCachePort(ABC):
    @abstractmethod
    async def find_candidates(
        self, embedding: QueryEmbedding, *, fingerprint: str, not_before: datetime, limit: int
    ) -> list[CacheCandidate]:
        """Nearest active entries (most similar first) made by the same model under the same fingerprint, not older
        than ``not_before``."""

    @abstractmethod
    async def store(self, entry: NewCacheEntry) -> None: ...

    @abstractmethod
    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        """Counts one more use of the entry and remembers when it was last served."""

    @abstractmethod
    async def flag_for_review(self, entry_id: uuid.UUID, *, deactivate: bool) -> bool:
        """Marks an entry for a human to look at, optionally stopping it from being served. False if it is gone."""

    @abstractmethod
    async def purge(self, *, keep_fingerprint: str, stale_before: datetime, unused_before: datetime) -> int:
        """Deletes entries unused since ``unused_before``, and entries made under another fingerprint that have not been
        used since ``stale_before``. Requiring "not used lately" means a caller that computes the wrong fingerprint
        (a differently configured process) can never remove an entry customers are still being served from. Entries
        flagged for review are kept until a person decides about them. Returns how many were removed."""
