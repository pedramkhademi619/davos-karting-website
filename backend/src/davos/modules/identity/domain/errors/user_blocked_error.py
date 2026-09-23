from davos.shared_kernel.domain.errors.permission_denied_error import PermissionDeniedError


class UserBlockedError(PermissionDeniedError):
    code = "user_blocked"

    def __init__(self) -> None:
        super().__init__("دسترسی این حساب کاربری محدود شده است.")
