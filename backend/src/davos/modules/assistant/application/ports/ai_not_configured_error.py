from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError


class AiNotConfiguredError(AiProviderError):
    """AI_BASE_URL / AI_API_KEY / AI_MODEL are not set; the assistant runs in fallback mode."""
