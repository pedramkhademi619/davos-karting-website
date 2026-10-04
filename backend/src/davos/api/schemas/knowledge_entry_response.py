from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.assistant.domain.entities.knowledge_entry import KnowledgeEntry


class KnowledgeEntryResponse(BaseModel):
    entry_id: uuid.UUID
    source_type: str
    title: str
    body: str
    url: str
    updated_at: datetime

    @classmethod
    def of(cls, entry: KnowledgeEntry) -> KnowledgeEntryResponse:
        return cls(
            entry_id=entry.entry_id,
            source_type=entry.source_type.value,
            title=entry.title,
            body=entry.body,
            url=entry.url,
            updated_at=entry.updated_at,
        )
