from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import httpx

from davos.modules.payments.adapters.mellat.mellat_response_codes import (
    ALREADY_REVERSED,
    ALREADY_SETTLED,
    ALREADY_VERIFIED,
    DEFINITELY_NOT_PAID,
    SUCCESS,
    describe,
)
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

_TEHRAN = timezone(timedelta(hours=3, minutes=30))
_SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
_SERVICE_NS = "http://interfaces.core.sw.bps.com/"
_MAX_ANSWER_BYTES = 64 * 1024


class MellatPaymentGateway(PaymentGatewayPort):
    """Bank Mellat (Behpardakht) IPG over its SOAP web service.

    Flow, as documented by Behpardakht:

    1. ``bpPayRequest`` returns ``"0,<RefId>"``; the browser is sent to ``startpay.mellat`` with a POST form carrying
       ``RefId``.
    2. The bank posts ``RefId, ResCode, SaleOrderId, SaleReferenceId`` back to the callback URL. ``ResCode`` other
       than 0 means the customer did not pay.
    3. ``bpVerifyRequest`` (0 = verified, 43 = already verified). When it answers anything else,
       ``bpInquiryRequest`` decides; if that also fails the customer did not pay (any hold is released with
       ``bpReversalRequest``).
    4. ``bpSettleRequest`` (0, or 45 = already settled) moves the money to the merchant; ``bpReversalRequest``
       instead returns it to the customer. The application decides which, after checking the order.

    Amounts are sent in Rial (the platform base unit). Card data from the callback is never read or stored, and the
    terminal password is never logged. The server's public IP must be registered with the bank, or every call answers
    code 421.
    """

    def __init__(
        self,
        *,
        http_client: httpx.AsyncClient,
        terminal_id: int,
        username: str,
        password: str,
        service_url: str,
        start_pay_url: str,
        timeout_seconds: float = 20.0,
    ) -> None:
        self._client = http_client
        self._terminal_id = terminal_id
        self._username = username
        self._password = password
        self._service_url = service_url
        self._start_pay_url = start_pay_url
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    @property
    def name(self) -> str:
        return "mellat"

    @property
    def is_configured(self) -> bool:
        return bool(self._terminal_id and self._username and self._password)

    async def request_payment(self, request: PaymentRequest) -> PaymentSession:
        now = datetime.now(_TEHRAN)
        answer = await self._call(
            "bpPayRequest",
            [
                ("terminalId", str(self._terminal_id)),
                ("userName", self._username),
                ("userPassword", self._password),
                ("orderId", str(request.gateway_order_id)),
                ("amount", str(request.amount.irr)),
                ("localDate", now.strftime("%Y%m%d")),
                ("localTime", now.strftime("%H%M%S")),
                ("additionalData", request.description[:100]),
                ("callBackUrl", request.callback_url),
                ("payerId", "0"),
            ],
        )
        code_text, _, ref_id = answer.partition(",")
        code = self._as_int(code_text)
        ref_id = ref_id.strip()
        if code != SUCCESS or not ref_id or len(ref_id) > 64 or not ref_id.isalnum():
            logger.warning("mellat bpPayRequest refused: %s", describe(code))
            raise GatewayRejectedError(code)
        return PaymentSession(
            authority=ref_id, redirect_url=self._start_pay_url, method="POST", form_fields={"RefId": ref_id}
        )

    async def verify_payment(self, request: VerificationRequest) -> VerificationResult:
        if request.gateway_order_id is None or not request.provider_reference:
            # Without SaleReferenceId there is nothing the bank can verify: the customer never completed the payment.
            return VerificationResult(VerificationOutcome.REJECTED)
        ids = self._ids(request.gateway_order_id, request.provider_reference)

        verify_code = self._as_int(await self._call("bpVerifyRequest", ids))
        if verify_code == SUCCESS:
            return VerificationResult(VerificationOutcome.VERIFIED, request.provider_reference, verify_code)
        if verify_code == ALREADY_VERIFIED:
            return VerificationResult(VerificationOutcome.ALREADY_VERIFIED, request.provider_reference, verify_code)

        inquiry_code = self._as_int(await self._call("bpInquiryRequest", ids))
        if inquiry_code == SUCCESS:
            return VerificationResult(VerificationOutcome.VERIFIED, request.provider_reference, verify_code)
        if inquiry_code not in DEFINITELY_NOT_PAID:
            logger.warning(
                "mellat: outcome unclear (verify %s, inquiry %s)", describe(verify_code), describe(inquiry_code)
            )
            raise GatewayUnavailableError
        logger.warning("mellat: not paid (verify %s, inquiry %s)", describe(verify_code), describe(inquiry_code))
        await self._best_effort_reverse(ids)
        return VerificationResult(VerificationOutcome.REJECTED, provider_code=verify_code)

    async def settle_payment(self, request: VerificationRequest) -> SettlementOutcome:
        ids = self._require_ids(request)
        code = self._as_int(await self._call("bpSettleRequest", ids))
        if code in {SUCCESS, ALREADY_SETTLED}:
            return SettlementOutcome.SETTLED
        if code in {ALREADY_REVERSED, 42, 54}:  # reversed, or the bank no longer has the sale
            return SettlementOutcome.REVERSED
        logger.warning("mellat settlement not confirmed (%s); will retry", describe(code))
        return SettlementOutcome.RETRY

    async def reverse_payment(self, request: VerificationRequest) -> bool:
        ids = self._require_ids(request)
        code = self._as_int(await self._call("bpReversalRequest", ids))
        if code in {SUCCESS, ALREADY_REVERSED}:
            return True
        if code is None:
            raise GatewayUnavailableError
        logger.error("mellat reversal refused: %s", describe(code))
        return False

    async def _best_effort_reverse(self, ids: list[tuple[str, str]]) -> None:
        try:
            await self._call("bpReversalRequest", ids)
        except (GatewayTimeoutError, GatewayUnavailableError):
            logger.info("mellat reversal of an unpaid attempt not sent; the bank releases unsettled holds itself")

    def _require_ids(self, request: VerificationRequest) -> list[tuple[str, str]]:
        if request.gateway_order_id is None or not request.provider_reference:
            raise GatewayRejectedError(None)
        return self._ids(request.gateway_order_id, request.provider_reference)

    def _ids(self, order_id: int, sale_reference_id: str) -> list[tuple[str, str]]:
        return [
            ("terminalId", str(self._terminal_id)),
            ("userName", self._username),
            ("userPassword", self._password),
            ("orderId", str(order_id)),
            ("saleOrderId", str(order_id)),
            ("saleReferenceId", sale_reference_id),
        ]

    async def _call(self, operation: str, parameters: list[tuple[str, str]]) -> str:
        envelope = ElementTree.Element(f"{{{_SOAP_NS}}}Envelope")
        body = ElementTree.SubElement(envelope, f"{{{_SOAP_NS}}}Body")
        call = ElementTree.SubElement(body, f"{{{_SERVICE_NS}}}{operation}")
        for name, value in parameters:
            ElementTree.SubElement(call, name).text = value
        payload = ElementTree.tostring(envelope, encoding="utf-8", xml_declaration=True)
        try:
            response = await self._client.post(
                self._service_url,
                content=payload,
                headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": ""},
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise GatewayTimeoutError from exc
        except httpx.TransportError as exc:
            raise GatewayUnavailableError from exc
        if response.status_code >= 500 or len(response.content) > _MAX_ANSWER_BYTES:
            logger.warning("mellat %s answered HTTP %s", operation, response.status_code)
            raise GatewayUnavailableError
        return self._return_value(response.content)

    @staticmethod
    def _return_value(content: bytes) -> str:
        if b"<!DOCTYPE" in content or b"<!ENTITY" in content:  # no entity expansion from any answer
            raise GatewayUnavailableError
        try:
            root = ElementTree.fromstring(content)  # noqa: S314 - DTDs are refused above; the answer comes over TLS
        except ElementTree.ParseError as exc:
            raise GatewayUnavailableError from exc
        for element in root.iter():
            if element.tag == "return" or element.tag.endswith("}return"):
                return (element.text or "").strip()
        raise GatewayUnavailableError

    @staticmethod
    def _as_int(value: str) -> int | None:
        try:
            return int(value.strip())
        except (AttributeError, ValueError):
            return None
