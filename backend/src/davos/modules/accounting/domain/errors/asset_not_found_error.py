from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class AssetNotFoundError(NotFoundError):
    code = "asset_not_found"

    def __init__(self, message: str = "دارایی پیدا نشد.") -> None:
        super().__init__(message)
