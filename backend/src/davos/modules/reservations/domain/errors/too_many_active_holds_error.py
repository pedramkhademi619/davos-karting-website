from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class TooManyActiveHoldsError(ConflictError):
    code = "too_many_active_holds"

    def __init__(self) -> None:
        super().__init__("چند رزرو پرداخت‌نشده دارید. اول آن‌ها را پرداخت یا لغو کنید.")
