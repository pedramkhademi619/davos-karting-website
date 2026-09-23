from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.application.ports.semantic_cache_port import SemanticCachePort
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding

# Every vector goes in as text and is cast on the server (CAST(CAST(:embedding AS text) AS vector)), so the async
# driver needs no custom type codec.

_FIND = text(
    """
    SELECT id, resolved_query, signature, response, sources,
           1 - (embedding <=> CAST(CAST(:embedding AS text) AS vector)) AS similarity
    FROM assistant_semantic_cache
    WHERE is_active
      AND fingerprint = :fingerprint
      AND embedding_model = :model
      AND created_at >= :not_before
    ORDER BY embedding <=> CAST(CAST(:embedding AS text) AS vector)
    LIMIT :limit
    """
)
_INSERT = text(
    """
    INSERT INTO assistant_semantic_cache
        (id, original_query, resolved_query, signature, embedding, embedding_model, fingerprint, response, sources,
         language, hit_count, is_active, is_flagged_for_review, created_at, last_used_at)
    VALUES
        (:id, :original_query, :resolved_query, :signature, CAST(CAST(:embedding AS text) AS vector), :model,
         :fingerprint, :response,
         CAST(CAST(:sources AS text) AS jsonb), :language, 0, true, false, :created_at, :created_at)
    """
)
_HIT = text("UPDATE assistant_semantic_cache SET hit_count = hit_count + 1, last_used_at = :at WHERE id = :id")
_FLAG = text(
    """
    UPDATE assistant_semantic_cache
    SET is_flagged_for_review = true, is_active = CASE WHEN :deactivate THEN false ELSE is_active END
    WHERE id = :id
    RETURNING id
    """
)
_PURGE = text(
    """
    DELETE FROM assistant_semantic_cache
    WHERE NOT is_flagged_for_review
      AND (last_used_at < :unused_before OR (fingerprint <> :keep_fingerprint AND last_used_at < :stale_before))
    """
)


def _literal(embedding: QueryEmbedding) -> str:
    return "[" + ",".join(repr(float(value)) for value in embedding.values) + "]"


class PgVectorSemanticCache(SemanticCachePort):
    """Stores cached answers in PostgreSQL and finds the nearest ones with pgvector's HNSW index (cosine distance)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_candidates(
        self, embedding: QueryEmbedding, *, fingerprint: str, not_before: datetime, limit: int
    ) -> list[CacheCandidate]:
        async with self._session_factory() as session, session.begin():
            # The filters above run after the index scan; iterative scanning keeps scanning until `limit` rows
            # survive them (pgvector 0.8+), so a busy table of stale entries cannot hide a fresh match.
            await session.execute(text("SET LOCAL hnsw.iterative_scan = 'strict_order'"))
            rows = await session.execute(
                _FIND,
                {
                    "embedding": _literal(embedding),
                    "fingerprint": fingerprint,
                    "model": embedding.model,
                    "not_before": not_before,
                    "limit": limit,
                },
            )
            return [self._candidate(row) for row in rows.mappings()]

    async def store(self, entry: NewCacheEntry) -> None:
        sources = json.dumps([{"title": s.title, "url": s.url} for s in entry.sources], ensure_ascii=False)
        async with self._session_factory() as session, session.begin():
            await session.execute(
                _INSERT,
                {
                    "id": entry.entry_id,
                    "original_query": entry.original_query,
                    "resolved_query": entry.resolved_query,
                    "signature": entry.signature,
                    "embedding": _literal(entry.embedding),
                    "model": entry.embedding.model,
                    "fingerprint": entry.fingerprint,
                    "response": entry.response,
                    "sources": sources,
                    "language": entry.language.value,
                    "created_at": entry.created_at,
                },
            )

    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(_HIT, {"id": entry_id, "at": at})

    async def flag_for_review(self, entry_id: uuid.UUID, *, deactivate: bool) -> bool:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(_FLAG, {"id": entry_id, "deactivate": deactivate})
            return result.scalar_one_or_none() is not None

    async def purge(self, *, keep_fingerprint: str, stale_before: datetime, unused_before: datetime) -> int:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(
                _PURGE,
                {"keep_fingerprint": keep_fingerprint, "stale_before": stale_before, "unused_before": unused_before},
            )
            return int(result.rowcount or 0)  # type: ignore[attr-defined]

    @staticmethod
    def _candidate(row: Any) -> CacheCandidate:
        raw_sources = row["sources"]
        sources = json.loads(raw_sources) if isinstance(raw_sources, str) else raw_sources
        return CacheCandidate(
            entry_id=row["id"],
            resolved_query=row["resolved_query"],
            signature=row["signature"],
            response=row["response"],
            sources=tuple(AnswerSource(title=s["title"], url=s["url"]) for s in sources),
            similarity=float(row["similarity"]),
        )
