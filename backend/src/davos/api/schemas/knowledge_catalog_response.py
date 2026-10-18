from __future__ import annotations

from pydantic import BaseModel

from davos.api.schemas.knowledge_entry_response import KnowledgeEntryResponse
from davos.modules.assistant.domain.value_objects.knowledge_catalog import KnowledgeCatalog


class KnowledgeCatalogResponse(BaseModel):
    entries: list[KnowledgeEntryResponse]
    max_entries: int
    max_chars: int
    total_chars: int
    sent_whole: bool

    @classmethod
    def of(cls, catalog: KnowledgeCatalog) -> KnowledgeCatalogResponse:
        return cls(
            entries=[KnowledgeEntryResponse.of(e) for e in catalog.entries],
            max_entries=catalog.max_entries,
            max_chars=catalog.max_chars,
            total_chars=catalog.total_chars,
            sent_whole=catalog.sent_whole,
        )
