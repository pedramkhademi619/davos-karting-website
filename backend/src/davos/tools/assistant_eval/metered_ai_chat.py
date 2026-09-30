from __future__ import annotations

import time

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.tools.assistant_eval.model_call import ModelCall


class MeteredAiChat(AIChatPort):
    """Records tokens, cache hits, cost and latency of every call; one instance per evaluated question."""

    def __init__(self, inner: AIChatPort, model: str) -> None:
        self._inner = inner
        self._model = model
        self.calls: list[ModelCall] = []

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        started = time.monotonic()
        try:
            completion = await self._inner.complete(request)
        except AiProviderError as exc:
            elapsed = time.monotonic() - started
            self.calls.append(ModelCall(self._model, 0, 0, 0, None, elapsed, failed=True, error=type(exc).__name__))
            raise
        usage = completion.usage
        self.calls.append(
            ModelCall(
                model=completion.model,
                prompt_tokens=usage.prompt_tokens,
                cached_prompt_tokens=usage.cached_prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cost_usd=completion.cost_usd,
                latency_s=time.monotonic() - started,
            )
        )
        return completion
