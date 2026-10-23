from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class OnlinePaymentPausedError(ConflictError):
    """A test copy of the site (PAYMENTS_PAUSED): nobody may start paying, so it is never mistaken for the real one."""

    code = "online_payment_paused"

    def __init__(self) -> None:
        super().__init__("در حال حاضر امکان رزرو اینترنتی وجود ندارد. با پشتیبانی تماس بگیرید.")
