from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class CashDayAlreadyClosedError(ConflictError):
    code = "cash_day_already_closed"

    def __init__(self, message: str = "صندوق این روز قبلا بسته شده است.") -> None:
        super().__init__(message)
