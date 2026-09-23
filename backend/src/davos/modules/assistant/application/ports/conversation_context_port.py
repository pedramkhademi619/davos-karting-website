from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.assistant.domain.value_objects.conversation_turn import ConversationTurn


class ConversationContextPort(ABC):
    """Short-lived memory of one conversation, only so that a follow-up can be understood. Never a permanent record."""

    @abstractmethod
    async def recent(self, conversation_id: uuid.UUID) -> tuple[ConversationTurn, ...]:
        """The latest exchanges, oldest first; empty when there are none or they expired."""

    @abstractmethod
    async def append(self, conversation_id: uuid.UUID, turn: ConversationTurn) -> None: ...

    @abstractmethod
    async def clear(self, conversation_id: uuid.UUID) -> None: ...
