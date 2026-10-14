from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class EntryAlreadyReversedError(ConflictError):
    code = "entry_already_reversed"

    def __init__(self, message: str = "این سند قبلا ابطال شده است.") -> None:
        super().__init__(message)
