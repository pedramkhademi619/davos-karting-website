from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidLineError(ValidationError):
    code = "invalid_line"

    def __init__(self, message: str = "هر سطر سند فقط یکی از بدهکار یا بستانکار را با مبلغ مثبت دارد.") -> None:
        super().__init__(message)
