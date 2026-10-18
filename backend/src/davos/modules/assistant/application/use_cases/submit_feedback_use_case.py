from __future__ import annotations

import uuid

from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.modules.assistant.application.services.semantic_answer_cache import SemanticAnswerCache
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class SubmitFeedbackUseCase:
    """Stores a customer's "was this helpful?" vote. A "no" about an answer that came from, or was saved in, the answer
    cache retires that stored answer at once, so nobody else is served it until a person has looked at it."""

    def __init__(self, *, interactions: InteractionLogPort, answer_cache: SemanticAnswerCache | None = None) -> None:
        self._interactions = interactions
        self._answer_cache = answer_cache

    async def execute(self, *, interaction_id: uuid.UUID, helpful: bool) -> None:
        recorded = await self._interactions.record_feedback(interaction_id, helpful=helpful)
        if recorded is None:
            raise NotFoundError("پاسخ موردنظر یافت نشد.")
        if not helpful and recorded.cache_entry_id is not None and self._answer_cache is not None:
            await self._answer_cache.deactivate(recorded.cache_entry_id)
