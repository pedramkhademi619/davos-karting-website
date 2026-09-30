from __future__ import annotations

import logging

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest

logger = logging.getLogger(__name__)


class FallbackAiChat(AIChatPort):
    """Asks a second model when the first one fails (outage, timeout, throttling, rejected request).

    Each side keeps its own circuit breaker, so a primary outage makes every question go straight to the backup until
    the primary recovers. If the backup fails too, the backup's error is raised and the FAQ fallback takes over.
    """

    def __init__(self, primary: AIChatPort, backup: AIChatPort) -> None:
        self._primary = primary
        self._backup = backup

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        try:
            return await self._primary.complete(request)
        except AiProviderError as exc:
            logger.warning("primary AI model failed (%s), asking the backup model", type(exc).__name__)
        return await self._backup.complete(request)
