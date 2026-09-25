from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class ReservationNotFoundError(NotFoundError):
    """Also used for reservations owned by someone else, so ids cannot be probed."""

    code = "reservation_not_found"

    def __init__(self) -> None:
        super().__init__("رزرو موردنظر یافت نشد.")
