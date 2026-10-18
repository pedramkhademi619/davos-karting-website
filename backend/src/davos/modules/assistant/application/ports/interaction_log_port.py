from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.assistant.application.ports.feedback_recorded import FeedbackRecorded
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction


class InteractionLogPort(ABC):
    @abstractmethod
    async def record(self, interaction: AssistantInteraction) -> None: ...

    @abstractmethod
    async def record_feedback(self, interaction_id: uuid.UUID, *, helpful: bool) -> FeedbackRecorded | None:
        """None when the interaction does not exist (or was already purged)."""

    @abstractmethod
    async def count_in_conversation(self, conversation_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def purge_expired(self, now: datetime) -> int:
        """Delete interactions past their retention date; returns the number removed."""
