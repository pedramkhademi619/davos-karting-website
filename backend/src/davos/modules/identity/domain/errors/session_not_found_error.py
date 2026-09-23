from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class SessionNotFoundError(NotFoundError):
    code = "session_not_found"

    def __init__(self) -> None:
        super().__init__("نشست موردنظر یافت نشد.")
