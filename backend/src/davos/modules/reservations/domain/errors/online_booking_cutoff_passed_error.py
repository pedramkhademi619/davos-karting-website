from datetime import time

from davos.shared_kernel.domain.errors.conflict_error import ConflictError

_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


class OnlineBookingCutoffPassedError(ConflictError):
    code = "online_booking_cutoff_passed"

    def __init__(self, cutoff: time) -> None:
        clock = cutoff.strftime("%H:%M").translate(_FA)
        super().__init__(
            f"رزرو آنلاین امروز تا ساعت {clock} باز بود. برای رزرو، لطفا حضوری به پیست مراجعه کنید یا تماس بگیرید."
        )
        self.cutoff = cutoff
