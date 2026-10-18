from __future__ import annotations

from davos.modules.assistant.application.ports.knowledge_index_port import KnowledgeIndexPort
from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


class InMemoryKnowledgeIndex(KnowledgeIndexPort):
    """Keeps entries the way the table would (one per type and ref) and records every call."""

    def __init__(self) -> None:
        self.entries: dict[tuple[KnowledgeSourceType, str], KnowledgeEntry] = {}
        self.upserts: list[KnowledgeEntry] = []
        self.removed: list[tuple[KnowledgeSourceType, str]] = []

    async def upsert(self, entry: KnowledgeEntry) -> None:
        self.upserts.append(entry)
        self.entries[(entry.source_type, entry.source_ref)] = entry

    async def remove(self, source_type: KnowledgeSourceType, source_ref: str) -> None:
        self.removed.append((source_type, source_ref))
        self.entries.pop((source_type, source_ref), None)

    async def refs_with_prefix(self, prefix: str) -> list[tuple[KnowledgeSourceType, str]]:
        return [key for key in self.entries if key[1].startswith(prefix)]

    async def count(self) -> int:
        return len(self.entries)

    @property
    def refs(self) -> set[str]:
        return {ref for _, ref in self.entries}
