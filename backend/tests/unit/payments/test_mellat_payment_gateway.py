"""Bank Mellat adapter against recorded SOAP answers (shape from the Behpardakht technical document)."""

from __future__ import annotations

import logging
from xml.etree import ElementTree

import httpx
import pytest
import respx

from davos.modules.payments.adapters.mellat.mellat_payment_gateway import MellatPaymentGateway
from davos.modules.payments.application.ports.gateway_rejected_error import GatewayRejectedError
from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError
from davos.modules.payments.application.ports.gateway_unavailable_error import GatewayUnavailableError
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.settlement_outcome import SettlementOutcome
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.shared_kernel.domain.money import Money

SERVICE = "https://bpm.test/pgwchannel/services/pgw"
START = "https://bpm.test/pgwchannel/startpay.mellat"
PASSWORD = "terminal-secret-password"
REQUEST = PaymentRequest("pay-1", "reservation:x", Money(7_900_000), "رزرو DK-ABC", "https://davos.test/cb", 1_000_042)
PAID = VerificationRequest(
    authority="REF123", amount=Money(7_900_000), gateway_order_id=1_000_042, provider_reference="98765"
)


def soap(operation: str, value: str) -> httpx.Response:
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/"><S:Body>'
        f'<ns2:{operation}Response xmlns:ns2="http://interfaces.core.sw.bps.com/"><return>{value}</return>'
        f"</ns2:{operation}Response></S:Body></S:Envelope>"
    )
    return httpx.Response(200, content=body.encode(), headers={"Content-Type": "text/xml"})


class Bank:
    """Answers per SOAP operation, in order; records every call."""

    def __init__(self, **answers: list[str] | Exception) -> None:
        self.answers = answers
        self.calls: list[tuple[str, dict[str, str]]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        root = ElementTree.fromstring(request.content)  # noqa: S314 - our own request
        body = next(e for e in root.iter() if e.tag.endswith("Body"))
        call = next(iter(body))
        operation = call.tag.split("}")[-1]
        self.calls.append((operation, {child.tag: child.text or "" for child in call}))
        script = self.answers[operation]
        if isinstance(script, Exception):
            raise script
        return soap(operation, script.pop(0) if len(script) > 1 else script[0])

    def operations(self) -> list[str]:
        return [name for name, _ in self.calls]


@pytest.fixture
async def client():
    async with httpx.AsyncClient() as c:
        yield c


def gateway(client: httpx.AsyncClient) -> MellatPaymentGateway:
    return MellatPaymentGateway(
        http_client=client,
        terminal_id=1234567,
        username="davos",
        password=PASSWORD,
        service_url=SERVICE,
        start_pay_url=START,
    )


@respx.mock
async def test_pay_request_sends_rials_and_our_order_id_and_returns_a_post_form(client, caplog) -> None:
    bank = Bank(bpPayRequest=["0,AF82041a2Bf6989c7fF9"])
    respx.post(SERVICE).mock(side_effect=bank)
    with caplog.at_level(logging.DEBUG):
        session = await gateway(client).request_payment(REQUEST)
    ((_, sent),) = bank.calls
    assert sent["amount"] == "7900000" and sent["orderId"] == "1000042"
    assert sent["terminalId"] == "1234567" and sent["callBackUrl"] == "https://davos.test/cb"
    assert len(sent["localDate"]) == 8 and len(sent["localTime"]) == 6
    assert session.authority == "AF82041a2Bf6989c7fF9" and session.method == "POST"
    assert session.redirect_url == START and session.form_fields == {"RefId": "AF82041a2Bf6989c7fF9"}
    assert PASSWORD not in caplog.text


@pytest.mark.parametrize("answer", ["21", "421", "0,", "0,not a ref!", "garbage"])
@respx.mock
async def test_a_refused_pay_request_is_a_rejection(client, answer: str) -> None:
    respx.post(SERVICE).mock(side_effect=Bank(bpPayRequest=[answer]))
    with pytest.raises(GatewayRejectedError):
        await gateway(client).request_payment(REQUEST)


@respx.mock
async def test_verification_uses_the_order_and_sale_reference_and_does_not_settle(client) -> None:
    bank = Bank(bpVerifyRequest=["0"])
    respx.post(SERVICE).mock(side_effect=bank)
    result = await gateway(client).verify_payment(PAID)
    assert result.outcome is VerificationOutcome.VERIFIED and result.reference_id == "98765"
    ((operation, sent),) = bank.calls
    assert operation == "bpVerifyRequest"  # settling is a separate decision of the application
    assert sent["orderId"] == sent["saleOrderId"] == "1000042" and sent["saleReferenceId"] == "98765"


@respx.mock
async def test_already_verified_is_a_success(client) -> None:
    respx.post(SERVICE).mock(side_effect=Bank(bpVerifyRequest=["43"]))
    assert (await gateway(client).verify_payment(PAID)).outcome is VerificationOutcome.ALREADY_VERIFIED


@respx.mock
async def test_a_failed_verify_is_decided_by_inquiry(client) -> None:
    bank = Bank(bpVerifyRequest=["415"], bpInquiryRequest=["0"])
    respx.post(SERVICE).mock(side_effect=bank)
    assert (await gateway(client).verify_payment(PAID)).outcome is VerificationOutcome.VERIFIED
    assert bank.operations() == ["bpVerifyRequest", "bpInquiryRequest"]


@respx.mock
async def test_a_definite_no_is_rejected_and_any_hold_is_released(client) -> None:
    bank = Bank(bpVerifyRequest=["17"], bpInquiryRequest=["17"], bpReversalRequest=["0"])
    respx.post(SERVICE).mock(side_effect=bank)
    result = await gateway(client).verify_payment(PAID)
    assert result.outcome is VerificationOutcome.REJECTED
    assert bank.operations() == ["bpVerifyRequest", "bpInquiryRequest", "bpReversalRequest"]


@pytest.mark.parametrize("unclear", ["34", "421", "416", "not-a-number"])
@respx.mock
async def test_an_unclear_answer_is_never_treated_as_not_paid(client, unclear: str) -> None:
    respx.post(SERVICE).mock(side_effect=Bank(bpVerifyRequest=[unclear], bpInquiryRequest=[unclear]))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).verify_payment(PAID)


async def test_without_a_sale_reference_there_is_nothing_to_verify(client) -> None:
    missing = VerificationRequest(authority="REF123", amount=Money(1), gateway_order_id=1, provider_reference=None)
    assert (await gateway(client).verify_payment(missing)).outcome is VerificationOutcome.REJECTED


@pytest.mark.parametrize(
    ("answer", "outcome"),
    [
        ("0", SettlementOutcome.SETTLED),
        ("45", SettlementOutcome.SETTLED),
        ("48", SettlementOutcome.REVERSED),
        ("34", SettlementOutcome.RETRY),
        ("46", SettlementOutcome.RETRY),
    ],
)
@respx.mock
async def test_settlement_answers(client, answer: str, outcome: SettlementOutcome) -> None:
    bank = Bank(bpSettleRequest=[answer])
    respx.post(SERVICE).mock(side_effect=bank)
    assert await gateway(client).settle_payment(PAID) is outcome
    assert bank.operations() == ["bpSettleRequest"]


@pytest.mark.parametrize(("answer", "reversed_"), [("0", True), ("48", True), ("54", False)])
@respx.mock
async def test_reversal_answers(client, answer: str, reversed_: bool) -> None:
    respx.post(SERVICE).mock(side_effect=Bank(bpReversalRequest=[answer]))
    assert await gateway(client).reverse_payment(PAID) is reversed_


@respx.mock
async def test_timeouts_and_outages_are_reported_as_such(client) -> None:
    respx.post(SERVICE).mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(GatewayTimeoutError):
        await gateway(client).verify_payment(PAID)
    respx.post(SERVICE).mock(return_value=httpx.Response(503, content=b"down"))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).settle_payment(PAID)


@respx.mock
async def test_entity_expansion_in_an_answer_is_refused(client) -> None:
    hostile = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "0">]><r><return>&a;</return></r>'
    respx.post(SERVICE).mock(return_value=httpx.Response(200, content=hostile))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).verify_payment(PAID)
