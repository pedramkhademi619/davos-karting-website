from davos.shared_kernel.domain.errors.domain_error import DomainError


class ValidationError(DomainError):
    code = "validation_error"
