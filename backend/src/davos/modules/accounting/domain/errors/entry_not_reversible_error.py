from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class EntryNotReversibleError(ConflictError):
    code = "entry_not_reversible"

    def __init__(self, message: str = "سند ابطال یا بستن سال را نمی‌شود دوباره ابطال کرد.") -> None:
        super().__init__(message)
