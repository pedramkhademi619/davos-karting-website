from __future__ import annotations

import logging
import time

import httpx

from davos.modules.assistant.application.ports.ai_chat_port import AIChatPort
from davos.modules.assistant.application.ports.ai_not_configured_error import AiNotConfiguredError
from davos.modules.assistant.application.ports.ai_provider_protocol_error import AiProviderProtocolError
from davos.modules.assistant.application.ports.ai_provider_rate_limited_error import AiProviderRateLimitedError
from davos.modules.assistant.application.ports.ai_provider_rejected_error import AiProviderRejectedError
from davos.modules.assistant.application.ports.ai_provider_timeout_error import AiProviderTimeoutError
from davos.modules.assistant.application.ports.ai_provider_unavailable_error import AiProviderUnavailableError
from davos.modules.assistant.application.ports.chat_completion import ChatCompletion
from davos.modules.assistant.application.ports.chat_completion_request import ChatCompletionRequest
from davos.modules.assistant.domain.value_objects.token_usage import TokenUsage

logger = logging.getLogger(__name__)

_CHARS_PER_TOKEN = 2


class OpenAICompatibleChatAdapter(AIChatPort):
    """Chat Completions client for any OpenAI-compatible provider.

    * base URL, key and model come from configuration; nothing provider-specific is hardcoded,
    * the token-limit parameter name is configurable (``max_tokens`` vs ``max_completion_tokens``), and a floor for
      it can be set for reasoning models, whose hidden thinking counts against the same limit,
    * prompts, answers and credentials are never logged, only status and latency,
    * every failure is mapped to a typed port error; raw provider bodies are dropped.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        http_client: httpx.AsyncClient,
        timeout_seconds: float,
        token_limit_param: str = "max_tokens",  # noqa: S107 - JSON field name, not a secret
        send_temperature: bool = True,
        min_output_tokens: int = 0,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/chat/completions" if base_url else ""
        self._api_key = api_key
        self._model = model
        self._client = http_client
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))
        self._token_limit_param = token_limit_param
        self._send_temperature = send_temperature
        self._min_output_tokens = min_output_tokens

    def __repr__(self) -> str:
        return f"OpenAICompatibleChatAdapter(model={self._model!r}, configured={self.is_configured})"

    @property
    def is_configured(self) -> bool:
        return bool(self._url and self._api_key and self._model)

    async def complete(self, request: ChatCompletionRequest) -> ChatCompletion:
        if not self.is_configured:
            raise AiNotConfiguredError("AI_BASE_URL, AI_API_KEY and AI_MODEL must be set")

        body: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": m.role.value, "content": m.content} for m in request.messages],
            self._token_limit_param: max(request.max_output_tokens, self._min_output_tokens),
        }
        if self._send_temperature:
            body["temperature"] = request.temperature

        started = time.monotonic()
        try:
            response = await self._client.post(
                self._url,
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise AiProviderTimeoutError("AI provider timed out") from exc
        except httpx.TransportError as exc:
            raise AiProviderUnavailableError("AI provider unreachable") from exc
        finally:
            logger.info("ai_call model=%s elapsed_ms=%d", self._model, (time.monotonic() - started) * 1000)

        self._raise_for_status(response)
        return self._parse(response, request)

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        status = response.status_code
        if status == 429:
            retry_after = response.headers.get("retry-after", "")
            raise AiProviderRateLimitedError(int(retry_after) if retry_after.isdigit() else None)
        if status >= 500:
            raise AiProviderUnavailableError(f"AI provider error (HTTP {status})")
        if status >= 400:
            raise AiProviderRejectedError(status)

    def _parse(self, response: httpx.Response, request: ChatCompletionRequest) -> ChatCompletion:
        try:
            payload = response.json()
            text = payload["choices"][0]["message"]["content"]
            if not isinstance(text, str):
                raise TypeError("content is not a string")
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise AiProviderProtocolError("AI provider returned an invalid completion") from exc

        usage = payload.get("usage") if isinstance(payload, dict) else None
        if isinstance(usage, dict) and isinstance(usage.get("prompt_tokens"), int):
            token_usage = TokenUsage(int(usage["prompt_tokens"]), int(usage.get("completion_tokens", 0) or 0))
        else:  # provider omitted usage: estimate so budgets still move
            prompt_chars = sum(len(m.content) for m in request.messages)
            token_usage = TokenUsage(prompt_chars // _CHARS_PER_TOKEN, len(text) // _CHARS_PER_TOKEN)
        return ChatCompletion(text=text, usage=token_usage, model=str(payload.get("model", self._model)))
