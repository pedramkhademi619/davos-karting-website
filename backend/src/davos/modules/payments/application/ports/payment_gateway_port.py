from abc import ABC, abstractmethod

from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.payment_session import PaymentSession
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.application.ports.verification_result import VerificationResult


class PaymentGatewayPort(ABC):
    @abstractmethod
    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        """Create a payment session.

        Raises GatewayRejectedError (do not retry), GatewayTimeoutError or GatewayUnavailableError.
        """

    @abstractmethod
    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        """Server-to-server verification, the only source of truth for success.

        A definitive negative answer returns ``REJECTED``. Timeouts and outages raise
        GatewayTimeoutError / GatewayUnavailableError, which callers must treat as UNKNOWN.
        """
