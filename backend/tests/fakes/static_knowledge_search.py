from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_search_port import KnowledgeSearchPort
from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery


class StaticKnowledgeSearch(KnowledgeSearchPort):
    """Canned passages. ``whole`` is what a small knowledge base hands over in full (empty means a large one)."""

    def __init__(
        self, passages: list[RetrievedPassage] | None = None, whole: list[RetrievedPassage] | None = None
    ) -> None:
        self.passages = passages or []
        self.whole = whole or []
        self.queries: list[SearchQuery] = []
        self.whole_requests: list[tuple[int, int]] = []

    async def search(self, query: SearchQuery, *, limit: int) -> list[RetrievedPassage]:
        self.queries.append(query)
        return self.passages[:limit]

    async def all_entries_if_small(
        self, query: SearchQuery, *, max_entries: int, max_total_chars: int
    ) -> list[RetrievedPassage]:
        self.whole_requests.append((max_entries, max_total_chars))
        return self.whole[:max_entries]
