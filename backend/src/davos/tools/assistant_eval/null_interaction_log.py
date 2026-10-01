from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.assistant.application.ports.feedback_recorded import FeedbackRecorded
from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction


class NullInteractionLog(InteractionLogPort):
    """Evaluation questions are not customer interactions: nothing is stored."""

    async def record(self, interaction: AssistantInteraction) -> None:
        return None

    async def record_feedback(self, interaction_id: uuid.UUID, *, helpful: bool) -> FeedbackRecorded | None:
        return None

    async def count_in_conversation(self, conversation_id: uuid.UUID) -> int:
        return 0

    async def purge_expired(self, now: datetime) -> int:
        return 0
