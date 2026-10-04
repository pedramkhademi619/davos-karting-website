from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry


class KnowledgeAdminPort(ABC):
    """The knowledge base as the staff panel edits it: the database is the only source of truth."""

    @abstractmethod
    async def list_all(self) -> list[KnowledgeEntry]:
        """By type, then title."""

    @abstractmethod
    async def get(self, entry_id: uuid.UUID) -> KnowledgeEntry | None: ...

    @abstractmethod
    async def add(self, entry: KnowledgeEntry) -> None: ...

    @abstractmethod
    async def save(self, entry: KnowledgeEntry) -> None:
        """Stores the new content of an entry that exists (same id; its source reference stays as it was)."""

    @abstractmethod
    async def delete(self, entry_id: uuid.UUID) -> bool:
        """False when there is no such entry."""
