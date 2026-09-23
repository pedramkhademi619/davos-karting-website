from __future__ import annotations

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


class ScriptedAiChat(AIChatPort):
    """Returns a canned reply (or raises a canned error) and records every request it receives."""

    def __init__(self, reply: str | BaseException = "", usage: TokenUsage | None = None) -> None:
        self.reply = reply
        self.usage = usage or TokenUsage(prompt_tokens=120, completion_tokens=30)
        self.requests: list[ChatCompletionRequest] = []

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        self.requests.append(request)
        if isinstance(self.reply, BaseException):
            raise self.reply
        return ChatCompletion(text=self.reply, usage=self.usage, model="fake-model")

    @property
    def calls(self) -> int:
        return len(self.requests)

    @property
    def system_prompt(self) -> str:
        return self.requests[-1].messages[0].content

    @property
    def user_prompt(self) -> str:
        return self.requests[-1].messages[1].content
