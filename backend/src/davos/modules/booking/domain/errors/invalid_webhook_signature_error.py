from davos.shared_kernel.domain.errors.domain_error import DomainError


class InvalidWebhookSignatureError(DomainError):
    """The reason is for logs only; callers always receive the same generic message."""

    code = "webhook_signature_invalid"

    def __init__(self, reason: str) -> None:
        super().__init__("امضای وب‌هوک معتبر نیست.")
        self.reason = reason
