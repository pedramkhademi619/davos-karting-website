from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.assistant.domain.value_objects.reviewed_interaction import ReviewedInteraction


class ReviewedInteractionResponse(BaseModel):
    interaction_id: uuid.UUID
    occurred_at: datetime
    outcome: str
    question_text: str | None
    answer_text: str | None
    helpful: bool | None
    served_from_cache: bool
    tokens: int

    @classmethod
    def of(cls, item: ReviewedInteraction) -> ReviewedInteractionResponse:
        return cls(
            interaction_id=item.interaction_id,
            occurred_at=item.occurred_at,
            outcome=item.outcome,
            question_text=item.question_text,
            answer_text=item.answer_text,
            helpful=item.helpful,
            served_from_cache=item.served_from_cache,
            tokens=item.tokens,
        )
