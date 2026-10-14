from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidAmountError(ValidationError):
    code = "invalid_amount"

    def __init__(self, message: str = "مبلغ باید یک عدد صحیح مثبت باشد.") -> None:
        super().__init__(message)
