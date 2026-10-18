from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ReviewedInteraction:
    """One stored question for review. The texts exist only when the customer agreed to have them kept."""

    interaction_id: uuid.UUID
    occurred_at: datetime
    outcome: str
    question_text: str | None
    answer_text: str | None
    helpful: bool | None
    served_from_cache: bool
    tokens: int
