class DomainError(Exception):
    """Base class for every business-rule violation.

    ``code`` is a stable machine-readable identifier used by the API layer to build
    error responses; ``message`` is safe to show to end users (Persian).
    """

    code: str = "domain_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
