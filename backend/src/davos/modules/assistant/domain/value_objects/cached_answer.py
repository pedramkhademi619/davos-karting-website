from __future__ import annotations

import uuid
from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource


@dataclass(frozen=True)
class CachedAnswer:
    entry_id: uuid.UUID
    text: str
    sources: tuple[AnswerSource, ...]
    similarity: float
