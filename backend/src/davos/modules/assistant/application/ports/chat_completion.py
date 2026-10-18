from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage


@dataclass(frozen=True)
class ChatCompletion:
    text: str
    usage: TokenUsage
    model: str
    cost_usd: float | None = None  # only when the provider reports it (some gateways do, OpenAI itself does not)
