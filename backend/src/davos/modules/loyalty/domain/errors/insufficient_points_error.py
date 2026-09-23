from davos.shared_kernel.domain.errors.conflict_error import ConflictError


class InsufficientPointsError(ConflictError):
    code = "insufficient_points"

    def __init__(self) -> None:
        super().__init__("امتیاز کافی برای این عملیات وجود ندارد.")
