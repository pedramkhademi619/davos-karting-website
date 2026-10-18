from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class AccountInUseError(ConflictError):
    code = "account_in_use"

    def __init__(self, message: str = "این حساب سند دارد یا زیرحساب دارد؛ فقط می‌توان آن را غیرفعال کرد.") -> None:
        super().__init__(message)
