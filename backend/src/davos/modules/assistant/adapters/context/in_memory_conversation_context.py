from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from davos.modules.assistant.application.ports.conversation_context_port import ConversationContextPort
from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn
from davos.shared_kernel.application.clock import Clock


class InMemoryConversationContext(ConversationContextPort):
    """Per-process memory for development and tests. Production uses Redis so every API replica sees the same one."""

    def __init__(self, clock: Clock, *, max_turns: int, ttl_seconds: int) -> None:
        self._clock = clock
        self._max_turns = max_turns
        self._ttl = timedelta(seconds=ttl_seconds)
        self._conversations: dict[uuid.UUID, tuple[datetime, list[ConversationTurn]]] = {}

    async def recent(self, conversation_id: uuid.UUID) -> tuple[ConversationTurn, ...]:
        entry = self._conversations.get(conversation_id)
        if entry is None or entry[0] < self._clock.now():
            self._conversations.pop(conversation_id, None)
            return ()
        return tuple(entry[1])

    async def append(self, conversation_id: uuid.UUID, turn: ConversationTurn) -> None:
        turns = [*(await self.recent(conversation_id)), turn][-self._max_turns :]
        self._conversations[conversation_id] = (self._clock.now() + self._ttl, turns)

    async def clear(self, conversation_id: uuid.UUID) -> None:
        self._conversations.pop(conversation_id, None)
