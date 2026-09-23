from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class PaymentNotFoundError(NotFoundError):
    """Also used for payments owned by someone else, so ids cannot be probed."""

    code = "payment_not_found"

    def __init__(self) -> None:
        super().__init__("پرداخت موردنظر یافت نشد.")
