from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class AccountNotFoundError(NotFoundError):
    code = "account_not_found"

    def __init__(self, message: str = "حساب پیدا نشد.") -> None:
        super().__init__(message)
