from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.shared_kernel.domain.errors.conflict_error import ConflictError

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


class DailyBookingLimitReachedError(ConflictError):
    code = "daily_booking_limit_reached"

    def __init__(self, mode: DailyBookingLimitMode, limit: int) -> None:
        what = "تعداد نفرات" if mode is DailyBookingLimitMode.PEOPLE else "تعداد تیکت‌های"
        super().__init__(
            f"ظرفیت رزرو آنلاین امروز پر شده (سقف {what} رزروشده: {str(limit).translate(_FA)}). "
            "برای رزرو حضوری مراجعه کنید یا با ما تماس بگیرید."
        )
        self.mode = mode
        self.limit = limit
