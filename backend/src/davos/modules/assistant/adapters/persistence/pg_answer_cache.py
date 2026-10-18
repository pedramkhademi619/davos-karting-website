from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.application.ports.answer_cache_port import AnswerCachePort
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate
from davos.modules.assistant.domain.value_objects.curated_answer import CURATED_FINGERPRINT
from davos.modules.assistant.domain.value_objects.new_cache_entry import NewCacheEntry
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding

# Every vector goes in as text and is cast on the server, so the async driver needs no custom type codec.
_FIND = text(
    """
    SELECT id, resolved_query, signature, response, sources,
           1 - (embedding <=> CAST(CAST(:embedding AS text) AS vector)) AS similarity
    FROM assistant_answer_cache
    WHERE is_active AND fingerprint IN (:fingerprint, :curated) AND embedding_model = :model
    ORDER BY embedding <=> CAST(CAST(:embedding AS text) AS vector)
    LIMIT :limit
    """
)
_INSERT = text(
    """
    INSERT INTO assistant_answer_cache
        (id, original_query, resolved_query, signature, embedding, embedding_model, fingerprint, response, sources,
         hit_count, is_active, created_at, last_used_at)
    VALUES
        (:id, :original_query, :resolved_query, :signature, CAST(CAST(:embedding AS text) AS vector), :model,
         :fingerprint, :response, CAST(CAST(:sources AS text) AS jsonb), 0, true, :created_at, :created_at)
    """
)
_REWRITE = text(
    """
    UPDATE assistant_answer_cache
    SET original_query = :original_query, resolved_query = :resolved_query, signature = :signature,
        embedding = CAST(CAST(:embedding AS text) AS vector), embedding_model = :model, fingerprint = :fingerprint,
        response = :response, sources = CAST(CAST(:sources AS text) AS jsonb), is_active = true
    WHERE id = :id
    """
)
_HIT = text("UPDATE assistant_answer_cache SET hit_count = hit_count + 1, last_used_at = :at WHERE id = :id")
_DEACTIVATE = text("UPDATE assistant_answer_cache SET is_active = false WHERE id = :id")


def _literal(embedding: QueryEmbedding) -> str:
    return "[" + ",".join(repr(value) for value in embedding.values) + "]"


class PgAnswerCache(AnswerCachePort):
    """Stores answers in PostgreSQL and finds the nearest ones with pgvector's cosine distance, exactly."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def find_candidates(
        self, embedding: QueryEmbedding, *, embedding_model: str, fingerprint: str, limit: int
    ) -> list[CacheCandidate]:
        async with self._session_factory() as session:
            rows = await session.execute(
                _FIND,
                {
                    "embedding": _literal(embedding),
                    "fingerprint": fingerprint,
                    "curated": CURATED_FINGERPRINT,
                    "model": embedding_model,
                    "limit": limit,
                },
            )
            return [self._candidate(row) for row in rows.mappings()]

    async def store(self, entry: NewCacheEntry) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(_INSERT, {**self._entry_values(entry), "created_at": entry.created_at})

    async def rewrite(self, entry: NewCacheEntry) -> bool:
        async with self._session_factory() as session, session.begin():
            result = await session.execute(_REWRITE, self._entry_values(entry))
            return bool(result.rowcount)  # type: ignore[attr-defined]

    async def record_hit(self, entry_id: uuid.UUID, at: datetime) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(_HIT, {"id": entry_id, "at": at})

    async def deactivate(self, entry_id: uuid.UUID) -> None:
        async with self._session_factory() as session, session.begin():
            await session.execute(_DEACTIVATE, {"id": entry_id})

    @staticmethod
    def _entry_values(entry: NewCacheEntry) -> dict[str, Any]:
        sources = json.dumps([{"title": s.title, "url": s.url} for s in entry.sources], ensure_ascii=False)
        return {
            "id": entry.entry_id,
            "original_query": entry.original_query,
            "resolved_query": entry.resolved_query,
            "signature": entry.signature,
            "embedding": _literal(entry.embedding),
            "model": entry.embedding_model,
            "fingerprint": entry.fingerprint,
            "response": entry.response,
            "sources": sources,
        }

    @staticmethod
    def _candidate(row: Any) -> CacheCandidate:
        raw_sources = row["sources"]
        sources = json.loads(raw_sources) if isinstance(raw_sources, str) else raw_sources
        return CacheCandidate(
            entry_id=row["id"],
            question=row["resolved_query"],
            signature=row["signature"],
            response=row["response"],
            sources=tuple(AnswerSource(title=s["title"], url=s["url"]) for s in sources),
            similarity=float(row["similarity"]),
        )
