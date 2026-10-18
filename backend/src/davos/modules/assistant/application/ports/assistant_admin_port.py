from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.assistant.application.ports.cached_answer_page import CachedAnswerPage
from davos.modules.assistant.application.ports.interaction_page import InteractionPage
from davos.modules.assistant.domain.value_objects.assistant_overview import AssistantOverview


class AssistantAdminPort(ABC):
    """Read and review side of the assistant, for the staff panel."""

    @abstractmethod
    async def overview(self, *, since: datetime, days: int) -> AssistantOverview: ...

    @abstractmethod
    async def interactions(
        self, *, outcomes: list[str], helpful: bool | None, with_text_only: bool, offset: int, limit: int
    ) -> InteractionPage:
        """Newest first. ``outcomes`` empty means every outcome; ``helpful`` filters on the customer's vote."""

    @abstractmethod
    async def cached_answers(
        self, *, active: bool | None, offset: int, limit: int, entry_id: uuid.UUID | None = None
    ) -> CachedAnswerPage:
        """Most used first; ``entry_id`` narrows the list to that one entry."""

    @abstractmethod
    async def set_cached_answer_active(self, entry_id: uuid.UUID, *, active: bool) -> bool:
        """False when there is no such entry."""

    @abstractmethod
    async def delete_cached_answer(self, entry_id: uuid.UUID) -> bool:
        """False when there is no such entry."""
