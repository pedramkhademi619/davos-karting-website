from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


@dataclass(frozen=True)
class RetrievedPassage:
    entry_id: uuid.UUID
    source_type: KnowledgeSourceType
    title: str
    text: str
    url: str
    score: float
