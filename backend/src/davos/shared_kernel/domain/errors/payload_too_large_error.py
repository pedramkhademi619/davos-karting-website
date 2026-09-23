from davos.shared_kernel.domain.errors.domain_error import DomainError


class PayloadTooLargeError(DomainError):
    code = "payload_too_large"

    def __init__(self) -> None:
        super().__init__("حجم درخواست بیش از حد مجاز است.")
