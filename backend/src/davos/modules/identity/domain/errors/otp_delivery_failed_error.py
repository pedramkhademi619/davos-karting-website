from davos.shared_kernel.domain.errors.domain_error import DomainError


class OtpDeliveryFailedError(DomainError):
    code = "otp_delivery_failed"

    def __init__(self) -> None:
        super().__init__("ارسال پیامک با مشکل مواجه شد. لطفا دوباره تلاش کنید.")
