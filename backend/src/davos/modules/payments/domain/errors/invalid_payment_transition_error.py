from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class InvalidPaymentTransitionError(ConflictError):
    code = "invalid_payment_transition"

    def __init__(self, current: str, attempted: str) -> None:
        super().__init__(f"وضعیت پرداخت از {current} به {attempted} قابل تغییر نیست.")
        self.current = current
        self.attempted = attempted
