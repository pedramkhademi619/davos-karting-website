from abc import ABC, abstractmethod

from davos.modules.assistant.domain.value_objects.retrieved_passage import RetrievedPassage
from davos.modules.assistant.domain.value_objects.search_query import SearchQuery


class KnowledgeSearchPort(ABC):
    @abstractmethod
    async def search(self, query: SearchQuery, *, limit: int) -> list[RetrievedPassage]:
        """Return published passages ranked by relevance, scores in [0, 1]. Never returns drafts."""

    @abstractmethod
    async def all_entries_if_small(
        self, query: SearchQuery, *, max_entries: int, max_total_chars: int
    ) -> list[RetrievedPassage]:
        """The whole published knowledge base, best match first, but only while it is small; otherwise an empty list.

        A handful of short entries fits comfortably in a prompt, and letting the model see all of it beats a keyword
        gate that misses casual phrasing or synonyms. The model must still cite a source, or its answer is discarded.
        """
