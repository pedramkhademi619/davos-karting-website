from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class YearAlreadyClosedError(ConflictError):
    code = "year_already_closed"

    def __init__(self, message: str = "این سال مالی قبلا بسته شده است.") -> None:
        super().__init__(message)
