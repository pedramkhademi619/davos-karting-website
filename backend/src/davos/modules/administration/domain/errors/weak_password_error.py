from davos.shared_kernel.domain.errors.validation_error import ValidationError


class WeakPasswordError(ValidationError):
    code = "weak_password"

    def __init__(self) -> None:
        super().__init__("رمز عبور باید حداقل ۱۲ نویسه و شامل حرف و عدد باشد.")
