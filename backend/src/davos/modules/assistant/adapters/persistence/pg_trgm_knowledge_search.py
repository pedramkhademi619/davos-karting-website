from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.modules.assistant.application.ports.knowledge_search_port import KnowledgeSearchPort
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery

_SEARCH_SQL = text(
    """
    SELECT id, source_type, title, body, url,
           GREATEST(word_similarity(CAST(:q AS text), title_norm),
                    word_similarity(CAST(:q AS text), search_text) * 0.9) AS score
    FROM assistant_knowledge_entries
    WHERE CAST(:q AS text) <% title_norm OR CAST(:q AS text) <% search_text
    ORDER BY score DESC, updated_at DESC
    LIMIT :limit
    """
)

_SIZE_SQL = text("SELECT count(*) AS entries, COALESCE(sum(length(body)), 0) AS chars FROM assistant_knowledge_entries")

_ALL_SQL = text(
    """
    SELECT id, source_type, title, body, url,
           GREATEST(word_similarity(CAST(:q AS text), title_norm),
                    word_similarity(CAST(:q AS text), search_text) * 0.9) AS score
    FROM assistant_knowledge_entries
    ORDER BY score DESC, updated_at DESC
    LIMIT :limit
    """
)


class PgTrgmKnowledgeSearch(KnowledgeSearchPort):
    """Persian-aware fuzzy retrieval using PostgreSQL trigram word similarity.

    Query and documents share PersianTextNormalizer output, so letter variants, ZWNJ and digit
    scripts do not affect matching. GIN trigram indexes keep it fast without an external engine.
    Embeddings are deliberately not used until measured recall on real questions justifies them.
    """

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession], *, word_similarity_threshold: float = 0.3
    ) -> None:
        self._session_factory = session_factory
        self._threshold = word_similarity_threshold

    async def search(self, query: SearchQuery, *, limit: int) -> list[RetrievedPassage]:
        if query.is_empty:
            return []
        async with self._session_factory() as session, session.begin():
            # SET LOCAL cannot take bind parameters; the value is a validated float, not user input.
            await session.execute(text(f"SET LOCAL pg_trgm.word_similarity_threshold = {float(self._threshold)}"))
            rows = (await session.execute(_SEARCH_SQL, {"q": query.match_text, "limit": limit})).all()
        return [
            RetrievedPassage(
                entry_id=uuid.UUID(str(row.id)),
                source_type=KnowledgeSourceType(row.source_type),
                title=row.title,
                text=row.body,
                url=row.url,
                score=float(row.score),
            )
            for row in rows
        ]

    async def all_entries_if_small(
        self, query: SearchQuery, *, max_entries: int, max_total_chars: int
    ) -> list[RetrievedPassage]:
        if query.is_empty:
            return []
        async with self._session_factory() as session, session.begin():
            size = (await session.execute(_SIZE_SQL)).one()
            if size.entries == 0 or size.entries > max_entries or size.chars > max_total_chars:
                return []
            rows = (await session.execute(_ALL_SQL, {"q": query.match_text, "limit": max_entries})).all()
        return [
            RetrievedPassage(
                entry_id=uuid.UUID(str(row.id)),
                source_type=KnowledgeSourceType(row.source_type),
                title=row.title,
                text=row.body,
                url=row.url,
                score=float(row.score),
            )
            for row in rows
        ]

    async def trigram_support_available(self) -> bool:
        """Readiness probe: fails when the database locale produces no trigrams for Persian text."""
        async with self._session_factory() as session:
            result = await session.execute(text("SELECT cardinality(show_trgm('کارتینگ')) > 0"))
            return bool(result.scalar_one())
