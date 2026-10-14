from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class DuplicateAccountCodeError(ConflictError):
    code = "duplicate_account_code"

    def __init__(self, message: str = "این کد حساب قبلا استفاده شده است.") -> None:
        super().__init__(message)
