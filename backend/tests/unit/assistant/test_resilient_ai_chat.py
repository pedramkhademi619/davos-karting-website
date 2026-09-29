import asyncio

import pytest

from davos.modules.assistant.adapters.ai.resilient_ai_chat import ResilientAiChat
from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_not_configured_error import AiNotConfiguredError
from davos.modules.assistant.application.ports.ai_provider_timeout_error import AiProviderTimeoutError
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.enums.chat_role import ChatRole
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage
from davos.platform.resilience.circuit_breaker import CircuitBreaker
from tests.fakes.scripted_ai_chat import ScriptedAiChat

REQUEST = ChatCompletionRequest(messages=(ChatMessage(ChatRole.USER, "hi"),), max_output_tokens=10, temperature=0.1)


def breaker(threshold: int = 2) -> CircuitBreaker:
    return CircuitBreaker(
        failure_threshold=threshold, recovery_seconds=60, is_failure=ResilientAiChat.counts_as_failure
    )


async def test_repeated_provider_failures_open_the_circuit_and_stop_calling_the_provider() -> None:
    inner = ScriptedAiChat(AiProviderTimeoutError())
    chat = ResilientAiChat(inner, breaker=breaker(2), max_concurrency=4, acquire_timeout_seconds=0.5)
    for _ in range(2):
        with pytest.raises(AiProviderTimeoutError):
            await chat.complete(REQUEST)
    with pytest.raises(AiProviderUnavailableError):
        await chat.complete(REQUEST)
    assert inner.calls == 2  # the third call never reached the provider


async def test_missing_configuration_does_not_open_the_circuit() -> None:
    inner = ScriptedAiChat(AiNotConfiguredError())
    chat = ResilientAiChat(inner, breaker=breaker(1), max_concurrency=4, acquire_timeout_seconds=0.5)
    for _ in range(3):
        with pytest.raises(AiNotConfiguredError):
            await chat.complete(REQUEST)
    assert inner.calls == 3


class _BlockingChat(AIChatPort):
    def __init__(self) -> None:
        self.release = asyncio.Event()
        self.started = 0

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        self.started += 1
        await self.release.wait()
        return ChatCompletion("ok", TokenUsage(1, 1), "m")


async def test_bulkhead_rejects_excess_concurrency_instead_of_queueing_forever() -> None:
    inner = _BlockingChat()
    chat = ResilientAiChat(inner, breaker=breaker(), max_concurrency=2, acquire_timeout_seconds=0.05)
    running = [asyncio.create_task(chat.complete(REQUEST)) for _ in range(2)]
    await asyncio.sleep(0.01)
    with pytest.raises(AiProviderUnavailableError):
        await chat.complete(REQUEST)
    assert inner.started == 2
    inner.release.set()
    assert [r.text for r in await asyncio.gather(*running)] == ["ok", "ok"]
    assert (await chat.complete(REQUEST)).text == "ok"  # capacity is released afterwards
