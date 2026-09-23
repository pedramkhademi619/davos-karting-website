from abc import ABC, abstractmethod

from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest


class AIChatPort(ABC):
    @abstractmethod
    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        """Return one completion or raise a subclass of ``AiProviderError``.

        Implementations must not log prompts or credentials and must enforce a timeout.
        """
