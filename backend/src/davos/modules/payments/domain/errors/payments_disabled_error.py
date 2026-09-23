from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class PaymentsDisabledError(NotFoundError):
    code = "payments_disabled"

    def __init__(self) -> None:
        super().__init__("پرداخت آنلاین در حال حاضر فعال نیست.")
