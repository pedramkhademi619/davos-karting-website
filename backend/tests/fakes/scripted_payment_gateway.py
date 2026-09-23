from __future__ import annotations

import asyncio

from davos.modules.payments.application.ports.gateway_error import GatewayError
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.payment_session import PaymentSession
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.application.ports.verification_result import VerificationResult


class ScriptedPaymentGateway(PaymentGatewayPort):
    """Scripted answers; records exactly what the application sent so tests can assert on it."""

    def __init__(self) -> None:
        self.authority = "A00000000000000000000000000000000001"
        self.request_error: GatewayError | None = None
        self.verify_results: list[VerificationResult | GatewayError] = [
            VerificationResult(VerificationOutcome.VERIFIED, reference_id="777")
        ]
        self.verify_delay = 0.0
        self.requests: list[PaymentRequest] = []
        self.verifications: list[VerificationRequest] = []

    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        self.requests.append(request)
        if self.request_error:
            raise self.request_error
        return PaymentSession(self.authority, f"https://pay.example.test/StartPay/{self.authority}")

    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        self.verifications.append(request)
        if self.verify_delay:
            await asyncio.sleep(self.verify_delay)
        result = self.verify_results.pop(0) if len(self.verify_results) > 1 else self.verify_results[0]
        if isinstance(result, GatewayError):
            raise result
        return result
