from __future__ import annotations

import logging
from typing import Any

import httpx

from davos.modules.payments.application.ports.gateway_rejected_error import GatewayRejectedError
from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError
from davos.modules.payments.application.ports.gateway_unavailable_error import GatewayUnavailableError
from davos.modules.payments.application.ports.payment_gateway_port import PaymentGatewayPort
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.payment_session import PaymentSession
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.modules.payments.application.ports.verification_result import VerificationResult

logger = logging.getLogger(__name__)

_CODE_SUCCESS = 100
_CODE_ALREADY_VERIFIED = 101


class ZarinpalPaymentGateway(PaymentGatewayPort):
    """Zarinpal v4 adapter (request.json / verify.json / StartPay).

    Contract taken from the official documentation (zarinpal.com/docs/paymentGateway):
    * amounts are sent as integers with ``currency`` stated explicitly as IRR, the platform base
      unit, so no Toman conversion can silently multiply or divide an amount;
    * code 100 = success, 101 = already verified, anything else is a definitive rejection;
    * card numbers / hashes returned by verification are deliberately discarded, only ``ref_id`` is kept.

    Not verified against the live sandbox in this repository (no merchant id available): see
    docs/LIMITATIONS.md. The contract is covered by respx-based adapter tests.
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient,
        merchant_id: str,
        sandbox: bool,
        api_host: str,
        sandbox_host: str,
        timeout_seconds: float = 10.0,
    ) -> None:
        self._client = http_client
        self._merchant_id = merchant_id
        self._host = (sandbox_host if sandbox else api_host).rstrip("/")
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    @property
    def name(self) -> str:
        return "zarinpal"

    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        body = {
            "merchant_id": self._merchant_id,
            "amount": request.amount.irr,
            "currency": "IRR",
            "description": request.description,
            "callback_url": request.callback_url,
            "metadata": {"order_id": str(request.gateway_order_id)},
        }
        data, errors = await self._post("/pg/v4/payment/request.json", body)
        code = self._code(data, errors)
        authority = data.get("authority") if isinstance(data, dict) else None
        if code != _CODE_SUCCESS or not isinstance(authority, str) or not authority:
            raise GatewayRejectedError(code)
        return PaymentSession(authority=authority, redirect_url=f"{self._host}/pg/StartPay/{authority}")

    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        body = {"merchant_id": self._merchant_id, "amount": request.amount.irr, "authority": request.authority}
        data, errors = await self._post("/pg/v4/payment/verify.json", body)
        code = self._code(data, errors)
        if code in {_CODE_SUCCESS, _CODE_ALREADY_VERIFIED}:
            ref_id = data.get("ref_id") if isinstance(data, dict) else None
            outcome = VerificationOutcome.VERIFIED if code == _CODE_SUCCESS else VerificationOutcome.ALREADY_VERIFIED
            return VerificationResult(
                outcome, reference_id=str(ref_id) if ref_id is not None else None, provider_code=code
            )
        if code is None:
            raise GatewayUnavailableError  # an answer without a code says nothing about the money
        return VerificationResult(VerificationOutcome.REJECTED, provider_code=code)

    async def settle_payment(self, request: VerificationRequest) -> SettlementOutcome:
        # Zarinpal captures the money on verification; there is no separate settlement step.
        return SettlementOutcome.SETTLED

    async def reverse_payment(self, request: VerificationRequest) -> bool:
        """Zarinpal's reverse.json returns a verified payment to the customer (within 30 minutes of the payment)."""
        body = {"merchant_id": self._merchant_id, "authority": request.authority}
        data, errors = await self._post("/pg/v4/payment/reverse.json", body)
        code = self._code(data, errors)
        if code is None:
            raise GatewayUnavailableError
        if code != _CODE_SUCCESS:
            logger.error("zarinpal reverse refused (code %s); refund this payment by hand", code)
        return code == _CODE_SUCCESS

    async def _post(self, path: str, body: dict[str, Any]) -> tuple[Any, Any]:
        try:
            response = await self._client.post(f"{self._host}{path}", json=body, timeout=self._timeout)
        except httpx.TimeoutException as exc:
            raise GatewayTimeoutError from exc
        except httpx.TransportError as exc:
            raise GatewayUnavailableError from exc
        if response.status_code >= 500:
            raise GatewayUnavailableError
        try:
            payload = response.json()
        except ValueError as exc:
            raise GatewayUnavailableError from exc
        if not isinstance(payload, dict):
            raise GatewayUnavailableError
        return payload.get("data"), payload.get("errors")

    @staticmethod
    def _code(data: Any, errors: Any) -> int | None:
        """Success carries ``data.code``; failures carry ``errors.code`` and an empty ``data`` list."""
        if isinstance(errors, dict) and isinstance(errors.get("code"), int):
            return int(errors["code"])
        if isinstance(data, dict) and isinstance(data.get("code"), int):
            return int(data["code"])
        return None
