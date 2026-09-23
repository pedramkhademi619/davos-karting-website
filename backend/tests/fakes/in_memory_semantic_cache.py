from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from davos.modules.assistant.application.ports.semantic_cache_port import SemanticCachePort
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass
class StoredEntry:
    entry: NewCacheEntry
    hit_count: int = 0
    is_active: bool = True
    is_flagged: bool = False
    last_used_at: datetime | None = field(default=None)


class InMemorySemanticCache(SemanticCachePort):
    """Same contract as the PostgreSQL adapter, with the cosine similarity computed in Python."""

    def __init__(self) -> None:
        self.entries: list[StoredEntry] = []
        self.fail_on_find = False
        self.fail_on_store = False

    async def find_candidates(
        self, embedding: QueryEmbedding, *, fingerprint: str, not_before: datetime, limit: int
    ) -> list[CacheCandidate]:
        if self.fail_on_find:
            raise RuntimeError("database is down")
        found = [
            CacheCandidate(
                entry_id=stored.entry.entry_id,
                resolved_query=stored.entry.resolved_query,
                signature=stored.entry.signature,
                response=stored.entry.response,
                sources=stored.entry.sources,
                similarity=sum(a * b for a, b in zip(stored.entry.embedding.values, embedding.values, strict=True)),
            )
            for stored in self.entries
            if stored.is_active
            and stored.entry.fingerprint == fingerprint
            and stored.entry.embedding.model == embedding.model
            and stored.entry.created_at >= not_before
        ]
        return sorted(found, key=lambda c: c.similarity, reverse=True)[:limit]

    async def store(self, entry: NewCacheEntry) -> None:
        if self.fail_on_store:
            raise RuntimeError("database is down")
        self.entries.append(StoredEntry(entry=entry))

    def _find(self, entry_id: uuid.UUID) -> StoredEntry | None:
        return next((s for s in self.entries if s.entry.entry_id == entry_id), None)

    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        if (stored := self._find(entry_id)) is not None:
            stored.hit_count += 1
            stored.last_used_at = at

    async def flag_for_review(self, entry_id: uuid.UUID, *, deactivate: bool) -> bool:
        stored = self._find(entry_id)
        if stored is None:
            return False
        stored.is_flagged = True
        stored.is_active = stored.is_active and not deactivate
        return True

    async def purge(self, *, keep_fingerprint: str, stale_before: datetime, unused_before: datetime) -> int:
        def removable(stored: StoredEntry) -> bool:
            last_used = stored.last_used_at or stored.entry.created_at
            other_fingerprint = stored.entry.fingerprint != keep_fingerprint
            return not stored.is_flagged and (
                last_used < unused_before or (other_fingerprint and last_used < stale_before)
            )

        before = len(self.entries)
        self.entries = [s for s in self.entries if not removable(s)]
        return before - len(self.entries)
