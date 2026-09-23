from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidBookingEventError(ValidationError):
    code = "invalid_booking_event"
