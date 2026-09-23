from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.assistant.domain.enums.language import Language
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource
from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass(frozen=True)
class NewCacheEntry:
    """A model answer about to be cached; ``fingerprint`` names the knowledge, notes, rules and model behind it."""

    entry_id: uuid.UUID
    original_query: str
    resolved_query: str
    signature: str
    embedding: QueryEmbedding
    fingerprint: str
    response: str
    sources: tuple[AnswerSource, ...]
    language: Language
    created_at: datetime
