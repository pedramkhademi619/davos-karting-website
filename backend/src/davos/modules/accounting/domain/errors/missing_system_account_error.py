from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class MissingSystemAccountError(ConflictError):
    code = "missing_system_account"

    def __init__(self, message: str = "حساب سیستمی لازم در سرفصل‌ها نیست؛ سرفصل‌ها را بررسی کنید.") -> None:
        super().__init__(message)
