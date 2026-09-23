from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class BookingOwnerMismatchError(ConflictError):
    """An event names a different customer for an already known booking: needs human review."""

    code = "booking_owner_mismatch"

    def __init__(self) -> None:
        super().__init__("مالک رزرو با رویداد دریافتی مطابقت ندارد.")
