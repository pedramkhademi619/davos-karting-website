from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class PeriodLockedError(ConflictError):
    code = "period_locked"

    def __init__(self, message: str = "این دوره حسابداری بسته شده است و سند تازه یا ابطال در آن ممکن نیست.") -> None:
        super().__init__(message)
