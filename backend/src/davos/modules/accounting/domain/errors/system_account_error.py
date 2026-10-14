from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class SystemAccountError(ConflictError):
    code = "system_account"

    def __init__(self, message: str = "حساب سیستمی را نمی‌شود حذف یا نوعش را عوض کرد.") -> None:
        super().__init__(message)
