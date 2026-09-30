from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class InvalidReservationTransitionError(ConflictError):
    code = "invalid_reservation_transition"

    def __init__(self, current: str, attempted: str) -> None:
        super().__init__("این تغییر برای وضعیت فعلی رزرو ممکن نیست.")
        self.current = current
        self.attempted = attempted
