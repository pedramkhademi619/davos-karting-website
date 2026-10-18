import pytest

from davos.modules.assistant.adapters.ai.fallback_ai_chat import FallbackAiChat
from davos.modules.assistant.application.ports.ai_provider_rate_limited_error import AiProviderRateLimitedError
from davos.modules.assistant.application.ports.ai_provider_timeout_error import AiProviderTimeoutError
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.enums.chat_role import ChatRole
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage
from tests.fakes.scripted_ai_chat import ScriptedAiChat

REQUEST = ChatCompletionRequest(messages=(ChatMessage(ChatRole.USER, "hi"),), max_output_tokens=10, temperature=0.1)


async def test_the_backup_is_not_called_when_the_primary_answers() -> None:
    primary, backup = ScriptedAiChat("اصلی"), ScriptedAiChat("پشتیبان")
    completion = await FallbackAiChat(primary, backup).complete(REQUEST)
    assert completion.text == "اصلی" and backup.calls == 0


@pytest.mark.parametrize(
    "error", [AiProviderTimeoutError(), AiProviderUnavailableError("x"), AiProviderRateLimitedError(3)]
)
async def test_the_backup_answers_when_the_primary_fails(error: Exception) -> None:
    primary, backup = ScriptedAiChat(error), ScriptedAiChat("پشتیبان")
    completion = await FallbackAiChat(primary, backup).complete(REQUEST)
    assert completion.text == "پشتیبان" and backup.requests == [REQUEST]


async def test_when_both_fail_the_backup_error_is_raised() -> None:
    chat = FallbackAiChat(ScriptedAiChat(AiProviderTimeoutError()), ScriptedAiChat(AiProviderUnavailableError("down")))
    with pytest.raises(AiProviderUnavailableError):
        await chat.complete(REQUEST)


async def test_programming_errors_are_not_hidden_by_the_backup() -> None:
    backup = ScriptedAiChat("پشتیبان")
    with pytest.raises(ValueError, match="bug"):
        await FallbackAiChat(ScriptedAiChat(ValueError("bug")), backup).complete(REQUEST)
    assert backup.calls == 0
