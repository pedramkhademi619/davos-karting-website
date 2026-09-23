from davos.modules.identity.domain.enums.otp_verification_result import OtpVerificationResult
from davos.shared_kernel.domain.errors.domain_error import DomainError


class OtpVerificationFailedError(DomainError):
    """Deliberately generic for callers so the API cannot be used to probe OTP state.

    The precise ``reason`` is kept for metrics and audit logs only.
    """

    code = "otp_verification_failed"

    def __init__(self, reason: OtpVerificationResult) -> None:
        super().__init__("کد تایید نادرست یا منقضی شده است.")
        self.reason = reason
