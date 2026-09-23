from __future__ import annotations

import uuid

from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.application.services.semantic_answer_cache import SemanticAnswerCache
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class SubmitFeedbackUseCase:
    def __init__(self, *, interactions: InteractionLogPort, cache: SemanticAnswerCache | None = None) -> None:
        self._interactions = interactions
        self._cache = cache

    async def execute(self, *, interaction_id: uuid.UUID, helpful: bool) -> None:
        if not await self._interactions.record_feedback(interaction_id, helpful=helpful):
            raise NotFoundError("پاسخ موردنظر یافت نشد.")
        if helpful or self._cache is None:
            return
        # A cached answer somebody found unhelpful must stop being repeated to others until a person reviews it.
        entry_id = await self._interactions.cache_entry_of(interaction_id)
        if entry_id is not None:
            await self._cache.flag_for_review(entry_id)
