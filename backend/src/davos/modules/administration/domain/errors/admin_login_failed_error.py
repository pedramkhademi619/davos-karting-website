from davos.shared_kernel.domain.errors.domain_error import DomainError


class AdminLoginFailedError(DomainError):
    """Same answer for an unknown username, a wrong password and a disabled account."""

    code = "admin_login_failed"

    def __init__(self) -> None:
        super().__init__("نام کاربری یا رمز عبور نادرست است.")
