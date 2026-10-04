from __future__ import annotations

import uuid
from datetime import timedelta

from davos.modules.assistant.application.ports.assistant_admin_port import AssistantAdminPort
from davos.modules.assistant.application.ports.cached_answer_page import CachedAnswerPage
from davos.modules.assistant.application.ports.interaction_page import InteractionPage
from davos.modules.assistant.domain.value_objects.assistant_overview import AssistantOverview
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class AssistantReviewUseCase:
    """The owner's view of the assistant: what it did, which answers customers found unhelpful or it could not give,
    and which answers are stored for reuse (retiring or deleting them)."""

    def __init__(self, *, admin: AssistantAdminPort, clock: Clock) -> None:
        self._admin = admin
        self._clock = clock

    async def overview(self, *, days: int) -> AssistantOverview:
        return await self._admin.overview(since=self._clock.now() - timedelta(days=days), days=days)

    async def interactions(
        self, *, outcomes: list[str], helpful: bool | None, with_text_only: bool, offset: int, limit: int
    ) -> InteractionPage:
        return await self._admin.interactions(
            outcomes=outcomes, helpful=helpful, with_text_only=with_text_only, offset=offset, limit=limit
        )

    async def cached_answers(
        self, *, active: bool | None, offset: int, limit: int, entry_id: uuid.UUID | None = None
    ) -> CachedAnswerPage:
        return await self._admin.cached_answers(active=active, offset=offset, limit=limit, entry_id=entry_id)

    async def set_cached_answer_active(self, entry_id: uuid.UUID, *, active: bool) -> None:
        if not await self._admin.set_cached_answer_active(entry_id, active=active):
            raise NotFoundError("پاسخ ذخیره‌شده یافت نشد.")

    async def delete_cached_answer(self, entry_id: uuid.UUID) -> None:
        if not await self._admin.delete_cached_answer(entry_id):
            raise NotFoundError("پاسخ ذخیره‌شده یافت نشد.")
