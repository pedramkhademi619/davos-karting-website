from __future__ import annotations

import asyncio

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_not_configured_error import AiNotConfiguredError
from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.platform.resilience.circuit_breaker import CircuitBreaker
from davos.platform.resilience.circuit_open_error import CircuitOpenError


class ResilientAiChat(AIChatPort):
    """Decorator adding a bulkhead (bounded concurrency) and a circuit breaker to any AIChatPort.

    AI traffic is isolated from the rest of the API: when the provider is slow or down, at most
    ``max_concurrency`` requests wait on it and further calls fail fast into the FAQ fallback.
    """

    def __init__(
        self,
        inner: AIChatPort,
        *,
        breaker: CircuitBreaker,
        max_concurrency: int,
        acquire_timeout_seconds: float = 0.5,
    ) -> None:
        self._inner = inner
        self._breaker = breaker
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._acquire_timeout = acquire_timeout_seconds

    @staticmethod
    def counts_as_failure(exc: BaseException) -> bool:
        """A missing configuration is not a provider outage and must not open the breaker."""
        return isinstance(exc, AiProviderError) and not isinstance(exc, AiNotConfiguredError)

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self._acquire_timeout)
        except TimeoutError as exc:
            raise AiProviderUnavailableError("AI concurrency limit reached") from exc
        try:
            return await self._breaker.call(lambda: self._inner.complete(request))
        except CircuitOpenError as exc:
            raise AiProviderUnavailableError("AI circuit breaker is open") from exc
        finally:
            self._semaphore.release()
