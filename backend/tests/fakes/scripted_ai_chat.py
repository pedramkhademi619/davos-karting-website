from __future__ import annotations

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


class ScriptedAiChat(AIChatPort):
    """Returns a canned reply (or raises a canned error) and records every request it receives.

    ``then`` lists the replies for the following calls, in order; after the last one ``reply`` is used again.
    """

    def __init__(
        self,
        reply: str | BaseException = "",
        usage: TokenUsage | None = None,
        then: list[str | BaseException] | None = None,
    ) -> None:
        self.reply = reply
        self.usage = usage or TokenUsage(prompt_tokens=120, completion_tokens=30)
        self.requests: list[ChatCompletionRequest] = []
        self._queue = [reply, *(then or [])] if then else []

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        self.requests.append(request)
        reply = self._queue.pop(0) if self._queue else self.reply
        if isinstance(reply, BaseException):
            raise reply
        return ChatCompletion(text=reply, usage=self.usage, model="fake-model")

    @property
    def calls(self) -> int:
        return len(self.requests)

    @property
    def system_prompt(self) -> str:
        return self.requests[-1].messages[0].content

    @property
    def user_prompt(self) -> str:
        return self.requests[-1].messages[1].content
