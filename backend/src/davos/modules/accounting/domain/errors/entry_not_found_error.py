from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class EntryNotFoundError(NotFoundError):
    code = "entry_not_found"

    def __init__(self, message: str = "سند پیدا نشد.") -> None:
        super().__init__(message)
