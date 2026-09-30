from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from davos.modules.assistant.domain.enums.answer_outcome import AnswerOutcome
from davos.modules.assistant.domain.value_objects.answer_source import AnswerSource


@dataclass(frozen=True)
class SupportAnswer:
    text: str
    outcome: AnswerOutcome
    sources: tuple[AnswerSource, ...] = field(default_factory=tuple)
    suggest_ticket: bool = False
    interaction_id: uuid.UUID | None = None
