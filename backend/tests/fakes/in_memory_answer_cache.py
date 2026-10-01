from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.assistant.application.ports.answer_cache_port import AnswerCachePort
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass
class StoredEntry:
    entry: NewCacheEntry
    active: bool = True
    hits: int = 0


class InMemoryAnswerCache(AnswerCachePort):
    """The answer store without a database; ``fail`` makes every call raise, like a database that is down."""

    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.entries: list[StoredEntry] = []

    def _check(self) -> None:
        if self.fail:
            raise ConnectionError("database is down")

    async def find_candidates(
        self, embedding: QueryEmbedding, *, embedding_model: str, fingerprint: str, limit: int
    ) -> list[CacheCandidate]:
        self._check()
        found = [
            CacheCandidate(
                entry_id=stored.entry.entry_id,
                question=stored.entry.resolved_query,
                signature=stored.entry.signature,
                response=stored.entry.response,
                sources=stored.entry.sources,
                similarity=sum(a * b for a, b in zip(embedding.values, stored.entry.embedding.values, strict=True)),
            )
            for stored in self.entries
            if stored.active
            and stored.entry.fingerprint == fingerprint
            and stored.entry.embedding_model == embedding_model
        ]
        return sorted(found, key=lambda c: c.similarity, reverse=True)[:limit]

    async def store(self, entry: NewCacheEntry) -> None:
        self._check()
        self.entries.append(StoredEntry(entry))

    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        self._check()
        for stored in self.entries:
            if stored.entry.entry_id == entry_id:
                stored.hits += 1

    async def deactivate(self, entry_id: uuid.UUID) -> None:
        self._check()
        for stored in self.entries:
            if stored.entry.entry_id == entry_id:
                stored.active = False
