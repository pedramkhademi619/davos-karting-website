from __future__ import annotations

import uuid
from datetime import datetime

from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.domain.entities.assistant_interaction import AssistantInteraction


class RecordingInteractionLog(InteractionLogPort):
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.items: list[AssistantInteraction] = []

    async def record(self, interaction: AssistantInteraction) -> None:
        if self.fail:
            raise RuntimeError("database is down")
        self.items.append(interaction)

    async def record_feedback(self, interaction_id: uuid.UUID, *, helpful: bool) -> bool:
        return any(i.interaction_id == interaction_id for i in self.items)

    async def cache_entry_of(self, interaction_id: uuid.UUID) -> uuid.UUID | None:
        return next((i.cache_entry_id for i in self.items if i.interaction_id == interaction_id), None)

    async def count_in_conversation(self, conversation_id: uuid.UUID) -> int:
        return sum(1 for i in self.items if i.conversation_id == conversation_id)

    async def purge_expired(self, now: datetime) -> int:
        before = len(self.items)
        self.items = [i for i in self.items if i.retention_until >= now]
        return before - len(self.items)
