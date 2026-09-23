from davos.shared_kernel.domain.errors.validation_error import ValidationError


class InvalidPointsEntryError(ValidationError):
    code = "invalid_points_entry"
