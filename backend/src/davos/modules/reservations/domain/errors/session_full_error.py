from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class SessionFullError(ConflictError):
    code = "session_full"

    def __init__(self, singles_left: int, doubles_left: int) -> None:
        super().__init__(f"ظرفیت این سانس کافی نیست. جای خالی: {singles_left} تک‌نفره و {doubles_left} دونفره.")
        self.singles_left = singles_left
        self.doubles_left = doubles_left
