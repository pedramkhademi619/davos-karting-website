from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError


class AiProviderRejectedError(AiProviderError):
    """4xx other than 429: bad credentials, unknown model, invalid request."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"AI provider rejected the request (HTTP {status_code})")
        self.status_code = status_code
