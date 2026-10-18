from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource


@dataclass(frozen=True)
class CacheCandidate:
    """A stored answer close to a new question, before the safety rules decide whether it may be served."""

    entry_id: uuid.UUID
    question: str  # the normalised question this answer was written for
    signature: str
    response: str
    sources: tuple[AnswerSource, ...]
    similarity: float  # cosine similarity of the two questions' embeddings, 1.0 = same meaning
