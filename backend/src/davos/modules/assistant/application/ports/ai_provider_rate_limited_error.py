from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError


class AiProviderRateLimitedError(AiProviderError):
    def __init__(self, retry_after_seconds: int | None = None) -> None:
        super().__init__("AI provider rate limited")
        self.retry_after_seconds = retry_after_seconds
