from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource


@dataclass(frozen=True)
class CacheCandidate:
    """A stored entry the vector search found near a question; ``similarity`` is cosine similarity (1 = identical)."""

    entry_id: uuid.UUID
    resolved_query: str
    signature: str
    response: str
    sources: tuple[AnswerSource, ...]
    similarity: float
