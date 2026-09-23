from davos.shared_kernel.domain.errors.domain_error import DomainError


class NotFoundError(DomainError):
    code = "not_found"
