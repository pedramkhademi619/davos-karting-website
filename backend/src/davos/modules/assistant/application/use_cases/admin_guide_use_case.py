from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.enums.chat_role import ChatRole
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage

logger = logging.getLogger(__name__)

_TURNS = 10  # the last messages of the conversation that are sent along
_MAX_CHARS = 1500
_UNAVAILABLE = "الان نمی‌توانم جواب بدهم؛ چند لحظه‌ی دیگر دوباره بپرسید. اگر فوری است، از مالک بپرسید."


class AdminGuideUseCase:
    """The panel's own helper for staff: answers "how do I do X in the panel?" from one written guide.

    It is deliberately apart from the customer assistant: no knowledge base, no answer cache, no stored chats, no
    customer data. The staff member's browser keeps the conversation and sends its last turns with every question.
    """

    def __init__(self, *, chat: AIChatPort, guide_file: str, max_output_tokens: int) -> None:
        self._chat = chat
        self._path = Path(guide_file)
        self._max_output_tokens = max_output_tokens
        self._guide: str | None = None

    def _text(self) -> str:
        if self._guide is None:
            self._guide = self._path.read_text(encoding="utf-8")
        return self._guide

    async def ask(self, conversation: Sequence[tuple[str, str]]) -> str:
        """``conversation``: (role, text) pairs, oldest first, the last one being the new question."""
        turns = [
            ChatMessage(ChatRole.ASSISTANT if role == "assistant" else ChatRole.USER, text.strip()[:_MAX_CHARS])
            for role, text in conversation[-_TURNS:]
            if text.strip()
        ]
        if not turns or turns[-1].role is not ChatRole.USER:
            return "سؤالتان را بنویسید تا کمک کنم."
        try:
            completion = await self._chat.complete(
                ChatCompletionRequest(
                    messages=(ChatMessage(ChatRole.SYSTEM, self._text()), *turns),
                    max_output_tokens=self._max_output_tokens,
                    temperature=0.2,
                )
            )
        except AiProviderError as exc:
            logger.info("admin guide unavailable: %s", type(exc).__name__)
            return _UNAVAILABLE
        return completion.text.strip() or _UNAVAILABLE
