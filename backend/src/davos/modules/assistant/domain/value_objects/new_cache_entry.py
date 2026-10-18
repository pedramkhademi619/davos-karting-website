from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass(frozen=True)
class NewCacheEntry:
    entry_id: uuid.UUID
    original_query: str
    resolved_query: str
    signature: str
    embedding: QueryEmbedding
    embedding_model: str
    fingerprint: str
    response: str
    sources: tuple[AnswerSource, ...]
    created_at: datetime
