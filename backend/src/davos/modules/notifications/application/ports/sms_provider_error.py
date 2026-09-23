class SmsProviderError(Exception):
    """Provider failure. ``retryable`` tells the queue whether another attempt makes sense."""

    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(message)
        self.retryable = retryable
