from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidMobileNumberError(ValidationError):
    code = "invalid_mobile_number"

    def __init__(self) -> None:
        super().__init__("شماره موبایل معتبر نیست.")
