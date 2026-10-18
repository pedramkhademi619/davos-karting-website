from __future__ import annotations

import json
import logging

import httpx
import pytest
import respx

from davos.modules.assistant.adapters.ai.openai_compatible_chat_adapter import OpenAICompatibleChatAdapter
from davos.modules.assistant.application.ports.ai_not_configured_error import AiNotConfiguredError
from davos.modules.assistant.application.ports.ai_provider_protocol_error import AiProviderProtocolError
from davos.modules.assistant.application.ports.ai_provider_rate_limited_error import AiProviderRateLimitedError
from davos.modules.assistant.application.ports.ai_provider_rejected_error import AiProviderRejectedError
from davos.modules.assistant.application.ports.ai_provider_timeout_error import AiProviderTimeoutError
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.enums.chat_role import ChatRole
from davos.modules.assistant.domain.value_objects.chat_message import ChatMessage

BASE = "https://ai.example.test/v1"
URL = f"{BASE}/chat/completions"
SECRET_KEY = "sk-test-SUPERSECRET123456"
REQUEST = ChatCompletionRequest(
    messages=(ChatMessage(ChatRole.SYSTEM, "rules"), ChatMessage(ChatRole.USER, "سلام")),
    max_output_tokens=200,
    temperature=0.1,
)


def make_adapter(client: httpx.AsyncClient, **overrides: object) -> OpenAICompatibleChatAdapter:
    values: dict[str, object] = {
        "base_url": BASE,
        "api_key": SECRET_KEY,
        "model": "configured-model",
        "http_client": client,
        "timeout_seconds": 5.0,
    }
    return OpenAICompatibleChatAdapter(**{**values, **overrides})  # type: ignore[arg-type]


def ok(content: str = "پاسخ [1]", usage: dict | None = None) -> httpx.Response:
    body: dict = {"model": "configured-model", "choices": [{"message": {"role": "assistant", "content": content}}]}
    if usage is not None:
        body["usage"] = usage
    return httpx.Response(200, json=body)


@pytest.fixture
async def client():
    async with httpx.AsyncClient() as c:
        yield c


@respx.mock
async def test_successful_completion_maps_text_usage_and_model(client: httpx.AsyncClient) -> None:
    respx.post(URL).mock(return_value=ok(usage={"prompt_tokens": 90, "completion_tokens": 12}))
    completion = await make_adapter(client).complete(REQUEST)
    assert completion.text == "پاسخ [1]"
    assert (completion.usage.prompt_tokens, completion.usage.completion_tokens) == (90, 12)


@respx.mock
async def test_request_uses_configured_model_auth_and_token_parameter(client: httpx.AsyncClient) -> None:
    route = respx.post(URL).mock(return_value=ok())
    await make_adapter(client).complete(REQUEST)
    sent = route.calls.last.request
    body = json.loads(sent.content)
    assert body["model"] == "configured-model"
    assert body["max_tokens"] == 200 and "max_completion_tokens" not in body
    assert body["messages"][1] == {"role": "user", "content": "سلام"}
    assert sent.headers["authorization"] == f"Bearer {SECRET_KEY}"


@respx.mock
async def test_token_parameter_name_and_temperature_are_configurable(client: httpx.AsyncClient) -> None:
    route = respx.post(URL).mock(return_value=ok())
    await make_adapter(client, token_limit_param="max_completion_tokens", send_temperature=False).complete(REQUEST)
    body = json.loads(route.calls.last.request.content)
    assert body["max_completion_tokens"] == 200 and "max_tokens" not in body and "temperature" not in body


@respx.mock
async def test_a_reasoning_model_can_be_given_a_larger_output_floor(client: httpx.AsyncClient) -> None:
    route = respx.post(URL).mock(return_value=ok())
    await make_adapter(client, min_output_tokens=2000).complete(REQUEST)
    assert json.loads(route.calls.last.request.content)["max_tokens"] == 2000
    await make_adapter(client, min_output_tokens=50).complete(REQUEST)
    assert json.loads(route.calls.last.request.content)["max_tokens"] == 200  # a floor, never a cut


@respx.mock
async def test_missing_usage_is_estimated_so_budgets_still_move(client: httpx.AsyncClient) -> None:
    respx.post(URL).mock(return_value=ok())
    completion = await make_adapter(client).complete(REQUEST)
    assert completion.usage.total > 0


@respx.mock
@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (httpx.Response(429, headers={"retry-after": "7"}, text="slow down"), AiProviderRateLimitedError),
        (httpx.Response(500, text="boom"), AiProviderUnavailableError),
        (httpx.Response(503, text="down"), AiProviderUnavailableError),
        (httpx.Response(401, text="bad key"), AiProviderRejectedError),
        (httpx.Response(404, text="unknown model"), AiProviderRejectedError),
        (httpx.Response(200, text="<html>not json</html>"), AiProviderProtocolError),
        (httpx.Response(200, json={"choices": []}), AiProviderProtocolError),
        (httpx.Response(200, json={"choices": [{"message": {"content": None}}]}), AiProviderProtocolError),
        (httpx.Response(200, json={"unexpected": True}), AiProviderProtocolError),
    ],
)
async def test_provider_responses_map_to_typed_errors(client: httpx.AsyncClient, response, expected) -> None:
    respx.post(URL).mock(return_value=response)
    with pytest.raises(expected):
        await make_adapter(client).complete(REQUEST)


@respx.mock
async def test_rate_limit_error_carries_retry_after(client: httpx.AsyncClient) -> None:
    respx.post(URL).mock(return_value=httpx.Response(429, headers={"retry-after": "7"}))
    with pytest.raises(AiProviderRateLimitedError) as info:
        await make_adapter(client).complete(REQUEST)
    assert info.value.retry_after_seconds == 7


@respx.mock
async def test_timeouts_and_transport_errors_are_distinguished(client: httpx.AsyncClient) -> None:
    respx.post(URL).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(AiProviderTimeoutError):
        await make_adapter(client).complete(REQUEST)
    respx.post(URL).mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(AiProviderUnavailableError):
        await make_adapter(client).complete(REQUEST)


@respx.mock
@pytest.mark.parametrize("missing", ["base_url", "api_key", "model"])
async def test_missing_configuration_fails_fast_without_any_http_call(client: httpx.AsyncClient, missing: str) -> None:
    route = respx.post(URL).mock(return_value=ok())
    with pytest.raises(AiNotConfiguredError):
        await make_adapter(client, **{missing: ""}).complete(REQUEST)
    assert not route.called


@respx.mock
async def test_secrets_prompts_and_provider_bodies_never_appear_in_logs_or_errors(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    respx.post(URL).mock(return_value=httpx.Response(500, text=f"upstream echoed {SECRET_KEY} and سلام"))
    adapter = make_adapter(client)
    with caplog.at_level(logging.DEBUG), pytest.raises(AiProviderUnavailableError) as info:
        await adapter.complete(REQUEST)
    haystack = caplog.text + str(info.value) + repr(adapter)
    assert SECRET_KEY not in haystack and "سلام" not in haystack


@respx.mock
async def test_cached_prompt_tokens_and_reported_cost_are_read(client: httpx.AsyncClient) -> None:
    usage = {
        "prompt_tokens": 3100,
        "completion_tokens": 60,
        "prompt_tokens_details": {"cached_tokens": 3060},
        "cost": 0.00012,
    }
    respx.post(URL).mock(return_value=ok(usage=usage))
    completion = await make_adapter(client).complete(REQUEST)
    assert completion.usage.cached_prompt_tokens == 3060
    assert completion.cost_usd == pytest.approx(0.00012)


@respx.mock
async def test_missing_cache_details_and_cost_mean_zero_and_unknown(client: httpx.AsyncClient) -> None:
    respx.post(URL).mock(return_value=ok(usage={"prompt_tokens": 90, "completion_tokens": 12, "cost": True}))
    completion = await make_adapter(client).complete(REQUEST)
    assert completion.usage.cached_prompt_tokens == 0
    assert completion.cost_usd is None
