class AiProviderError(Exception):
    """Base for every failure of the AI provider. Raw provider payloads are never attached."""

    def __init__(self, message: str = "AI provider error") -> None:
        super().__init__(message)
