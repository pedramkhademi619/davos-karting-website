from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.cached_answer_record import CachedAnswerRecord


@dataclass(frozen=True)
class CachedAnswerPage:
    items: list[CachedAnswerRecord]
    total: int
