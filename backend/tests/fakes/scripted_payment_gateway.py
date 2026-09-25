from __future__ import annotations

import asyncio

from davos.modules.payments.application.ports.gateway_error import GatewayError
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.payment_session import PaymentSession
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
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
        self.settle_results: list[SettlementOutcome | GatewayError] = [SettlementOutcome.SETTLED]
        self.reverse_results: list[bool | GatewayError] = [True]
        self.verify_delay = 0.0
        self.requests: list[PaymentRequest] = []
        self.verifications: list[VerificationRequest] = []
        self.settlements: list[VerificationRequest] = []
        self.reversals: list[VerificationRequest] = []

    @property
    def name(self) -> str:
        return "scripted"

    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        self.requests.append(request)
        if self.request_error:
            raise self.request_error
        return PaymentSession(self.authority, f"https://pay.example.test/StartPay/{self.authority}")

    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        self.verifications.append(request)
        if self.verify_delay:
            await asyncio.sleep(self.verify_delay)
        return self._next(self.verify_results)

    async def settle_payment(self, request: VerificationRequest) -> SettlementOutcome:
        self.settlements.append(request)
        return self._next(self.settle_results)

    async def reverse_payment(self, request: VerificationRequest) -> bool:
        self.reversals.append(request)
        return self._next(self.reverse_results)

    @staticmethod
    def _next[T](script: list[T | GatewayError]) -> T:
        result = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(result, GatewayError):
            raise result
        return result
