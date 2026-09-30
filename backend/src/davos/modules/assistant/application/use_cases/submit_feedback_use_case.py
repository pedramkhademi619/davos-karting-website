from __future__ import annotations

import uuid

from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class SubmitFeedbackUseCase:
    def __init__(self, *, interactions: InteractionLogPort) -> None:
        self._interactions = interactions

    async def execute(self, *, interaction_id: uuid.UUID, helpful: bool) -> None:
        if not await self._interactions.record_feedback(interaction_id, helpful=helpful):
            raise NotFoundError("پاسخ موردنظر یافت نشد.")
