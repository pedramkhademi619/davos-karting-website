from davos.shared_kernel.domain.errors.domain_error import DomainError


class ConflictError(DomainError):
    code = "conflict"
