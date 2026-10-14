from davos.shared_kernel.domain.errors.validation_error import ValidationError


class EmptyEntryError(ValidationError):
    code = "empty_entry"

    def __init__(self, message: str = "هر سند حداقل دو سطر با مبلغ دارد.") -> None:
        super().__init__(message)
