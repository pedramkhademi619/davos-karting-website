from abc import ABC, abstractmethod

from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry
from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


class KnowledgeIndexPort(ABC):
    @abstractmethod
    async def upsert(self, entry: KnowledgeEntry) -> None:
        """Insert or update by (source_type, source_ref). Idempotent."""

    @abstractmethod
    async def remove(self, source_type: KnowledgeSourceType, source_ref: str) -> None:
        """Idempotent removal used when content is unpublished or deleted."""

    @abstractmethod
    async def refs_with_prefix(self, prefix: str) -> list[tuple[KnowledgeSourceType, str]]:
        """(type, source_ref) of every entry whose ref starts with ``prefix``, so a sync can remove what is unwanted."""

    @abstractmethod
    async def count(self) -> int:
        """How many entries exist, whoever published them."""
