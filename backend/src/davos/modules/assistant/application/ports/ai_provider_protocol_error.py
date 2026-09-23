from davos.modules.assistant.application.ports.ai_provider_error import AiProviderError


class AiProviderProtocolError(AiProviderError):
    """Response was not a valid chat completion."""
