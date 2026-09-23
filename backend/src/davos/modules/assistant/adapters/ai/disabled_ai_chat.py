from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_not_configured_error import AiNotConfiguredError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest


class DisabledAiChat(AIChatPort):
    """Used when no provider is configured: the assistant degrades to FAQ links, it never fakes answers."""

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        raise AiNotConfiguredError("AI provider is not configured")
