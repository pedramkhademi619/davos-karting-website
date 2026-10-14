from davos.shared_kernel.domain.errors.validation_error import ValidationError


class AccountNotPostableError(ValidationError):
    code = "account_not_postable"

    def __init__(self, message: str = "روی حساب‌های گروه (سرفصل) یا غیرفعال نمی‌شود سند زد.") -> None:
        super().__init__(message)
