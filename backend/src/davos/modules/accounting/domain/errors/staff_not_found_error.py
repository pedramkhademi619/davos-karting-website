from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class StaffNotFoundError(NotFoundError):
    code = "staff_not_found"

    def __init__(self, message: str = "این کارمند پیدا نشد.") -> None:
        super().__init__(message)
