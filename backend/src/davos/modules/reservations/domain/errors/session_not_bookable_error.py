from davos.shared_kernel.domain.errors.validation_error import ValidationError


class SessionNotBookableError(ValidationError):
    code = "session_not_bookable"

    def __init__(self) -> None:
        super().__init__("این روز یا ساعت برای رزرو آنلاین باز نیست.")
