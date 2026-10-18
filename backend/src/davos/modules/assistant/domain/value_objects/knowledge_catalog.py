from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry


@dataclass(frozen=True)
class KnowledgeCatalog:
    """Every published entry, with how it fits the limit for sending the whole base to the model.

    Up to ``max_entries`` entries and ``max_chars`` characters the whole base rides in every prompt, which keeps casual
    questions answerable; beyond that the assistant falls back to keyword retrieval (docs/ASSISTANT_EVALUATION.md).
    """

    entries: tuple[KnowledgeEntry, ...]
    max_entries: int
    max_chars: int

    @property
    def total_chars(self) -> int:
        return sum(len(entry.body) for entry in self.entries)

    @property
    def sent_whole(self) -> bool:
        return 0 < len(self.entries) <= self.max_entries and self.total_chars <= self.max_chars
