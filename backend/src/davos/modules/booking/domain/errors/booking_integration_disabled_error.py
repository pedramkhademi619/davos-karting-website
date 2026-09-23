from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class BookingIntegrationDisabledError(NotFoundError):
    code = "booking_integration_disabled"

    def __init__(self) -> None:
        super().__init__("اتصال به سامانه رزرو فعال نیست.")
