from abc import ABC, abstractmethod

from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.payment_session import PaymentSession
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.application.ports.verification_result import VerificationResult


class PaymentGatewayPort(ABC):
    """Bank gateway. Verification, settlement and reversal are separate so the application can decide in between
    whether the order may still take the money."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier stored with every attempt (for example ``mellat``)."""

    @abstractmethod
    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        """Create a payment session.

        Raises GatewayRejectedError (do not retry), GatewayTimeoutError or GatewayUnavailableError.
        """

    @abstractmethod
    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        """Server-to-server verification, the only source of truth that the customer paid.

        A definitive negative answer returns ``REJECTED``. Timeouts and outages raise GatewayTimeoutError /
        GatewayUnavailableError, which callers must treat as UNKNOWN.
        """

    @abstractmethod
    async def settle_payment(self, request: VerificationRequest) -> SettlementOutcome:
        """Move verified funds to the merchant. Gateways that capture on verification answer SETTLED at once.

        Raises GatewayTimeoutError / GatewayUnavailableError when the answer is not known (retry later).
        """

    @abstractmethod
    async def reverse_payment(self, request: VerificationRequest) -> bool:
        """Give a verified, unsettled payment back to the customer. True when the bank confirmed the reversal.

        Raises GatewayTimeoutError / GatewayUnavailableError when the answer is not known (retry later).
        """
