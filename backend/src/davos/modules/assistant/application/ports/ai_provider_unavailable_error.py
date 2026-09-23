from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError


class AiProviderUnavailableError(AiProviderError):
    """Transport failure, 5xx, open circuit breaker or local concurrency limit reached."""
