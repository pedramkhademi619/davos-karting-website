from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class ShiftAlreadyStartedError(ConflictError):
    code = "shift_already_started"

    def __init__(self) -> None:
        super().__init__(
            "شیفت این سانس شروع شده و رزرو آنلاین آن بسته است. "
            "شیفت بعدی را انتخاب کنید، یا حضوری به پیست مراجعه کنید یا تماس بگیرید."
        )
