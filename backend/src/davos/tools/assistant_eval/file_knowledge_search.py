from __future__ import annotations

import uuid
from dataclasses import replace

from davos.modules.assistant.application.ports.knowledge_document_source_port import KnowledgeDocumentSourcePort
from davos.modules.assistant.application.ports.knowledge_search_port import KnowledgeSearchPort
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery

_ID_NAMESPACE = uuid.UUID("5a1e7c0d-0000-4000-8000-0000000e7a15")


class FileKnowledgeSearch(KnowledgeSearchPort):
    """The published knowledge files, searched in memory, so an evaluation needs no database.

    It mirrors production's small-knowledge-base branch (every published entry is sent) and ranks entries the way
    ``PgTrgmKnowledgeSearch`` roughly does, by the share of query words found in the entry, best match first. The
    trigram search itself is therefore not what is evaluated; it only matters once the knowledge base outgrows
    ``whole_knowledge_max_chars``.
    """

    def __init__(self, source: KnowledgeDocumentSourcePort, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()
        documents = [d for d in source.read_all().documents if d.published]
        self._passages = [
            RetrievedPassage(uuid.uuid5(_ID_NAMESPACE, d.ref), d.source_type, d.title, d.body, d.url, 0.0)
            for d in sorted(documents, key=lambda d: d.ref)
        ]
        self._texts = [self._normalizer.normalize(f"{p.title} {p.text}") for p in self._passages]

    @property
    def passages(self) -> list[RetrievedPassage]:
        return list(self._passages)

    async def search(self, query: SearchQuery, *, limit: int) -> list[RetrievedPassage]:
        return self._ranked(query)[:limit]

    async def all_entries_if_small(
        self, query: SearchQuery, *, max_entries: int, max_total_chars: int
    ) -> list[RetrievedPassage]:
        if len(self._passages) > max_entries or sum(len(p.text) for p in self._passages) > max_total_chars:
            return []
        return self._ranked(query)

    def _ranked(self, query: SearchQuery) -> list[RetrievedPassage]:
        words = set(query.tokens)
        scored = []
        for passage, text in zip(self._passages, self._texts, strict=True):
            score = sum(1 for w in words if w in text) / len(words) if words else 0.0
            scored.append(replace(passage, score=round(score, 3)))
        return sorted(scored, key=lambda p: p.score, reverse=True)
