from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage


@dataclass(frozen=True)
class ChatCompletionRequest:
    messages: tuple[ChatMessage, ...]
    max_output_tokens: int
    temperature: float = 0.1
