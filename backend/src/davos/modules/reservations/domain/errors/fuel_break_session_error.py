from davos.shared_kernel.domain.errors.validation_error import ValidationError


class FuelBreakSessionError(ValidationError):
    """A session at a blocked minute of the hour (ScheduleSettings.blocked_minutes): karts are being refuelled then,
    never sold -- online or at the counter."""

    code = "fuel_break_session"

    def __init__(self) -> None:
        super().__init__("این سانس برای سوخت‌گیری خودروها تعطیل است و قابل رزرو نیست.")
