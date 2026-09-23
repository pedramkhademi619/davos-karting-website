from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


@dataclass(frozen=True)
class ChatCompletion:
    text: str
    usage: TokenUsage
    model: str
