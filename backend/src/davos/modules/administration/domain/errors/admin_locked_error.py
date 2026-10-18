from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError


class AdminLockedError(RateLimitedError):
    code = "admin_locked"

    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(
            "به دلیل تلاش‌های ناموفق، ورود این حساب موقتا بسته است. کمی بعد دوباره تلاش کنید.",
            retry_after_seconds=retry_after_seconds,
        )
