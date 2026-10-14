from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class VendorNotFoundError(NotFoundError):
    code = "vendor_not_found"

    def __init__(self, message: str = "تامین‌کننده پیدا نشد.") -> None:
        super().__init__(message)
