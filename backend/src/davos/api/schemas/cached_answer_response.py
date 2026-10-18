from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.assistant.domain.value_objects.cached_answer_record import CachedAnswerRecord


class CachedAnswerResponse(BaseModel):
    entry_id: uuid.UUID
    question: str
    answer: str
    hit_count: int
    is_active: bool
    is_curated: bool
    created_at: datetime
    last_used_at: datetime

    @classmethod
    def of(cls, record: CachedAnswerRecord) -> CachedAnswerResponse:
        return cls(
            entry_id=record.entry_id,
            question=record.question,
            answer=record.answer,
            hit_count=record.hit_count,
            is_active=record.is_active,
            is_curated=record.is_curated,
            created_at=record.created_at,
            last_used_at=record.last_used_at,
        )
