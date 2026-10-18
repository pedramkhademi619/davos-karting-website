from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class OnlineBookingClosedError(ConflictError):
    code = "online_booking_closed"

    def __init__(self) -> None:
        super().__init__("رزرو آنلاین فعلا بسته است. برای رزرو تماس بگیرید.")
