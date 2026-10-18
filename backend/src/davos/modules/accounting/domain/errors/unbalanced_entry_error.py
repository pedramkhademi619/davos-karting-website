from davos.shared_kernel.domain.errors.validation_error import ValidationError


class UnbalancedEntryError(ValidationError):
    code = "unbalanced_entry"

    def __init__(self, message: str = "سند تراز نیست: جمع بدهکار و بستانکار باید برابر باشد.") -> None:
        super().__init__(message)
