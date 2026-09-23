from davos.shared_kernel.domain.errors.domain_error import DomainError


class PermissionDeniedError(DomainError):
    code = "permission_denied"
