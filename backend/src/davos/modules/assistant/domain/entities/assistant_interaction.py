from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


@dataclass(frozen=True)
class AssistantInteraction:
    """Audit record of one question. Text is present only when the customer consented to storage."""

    interaction_id: uuid.UUID
    occurred_at: datetime
    outcome: AnswerOutcome
    usage: TokenUsage
    source_entry_ids: tuple[uuid.UUID, ...]
    retention_until: datetime
    conversation_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    question_text: str | None = None
    answer_text: str | None = None
    # The semantic cache entry this answer was served from (a hit) or produced (a miss that was cached).
    cache_entry_id: uuid.UUID | None = None
    served_from_cache: bool = False
    helpful: bool | None = field(default=None, compare=False)
