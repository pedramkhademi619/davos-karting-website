from __future__ import annotations

import json
import logging

import httpx
import pytest
import respx

from davos.modules.payments.adapters.zarinpal.zarinpal_payment_gateway import ZarinpalPaymentGateway
from davos.modules.payments.application.ports.gateway_rejected_error import GatewayRejectedError
from davos.modules.payments.application.ports.gateway_timeout_error import GatewayTimeoutError
from davos.modules.payments.application.ports.gateway_unavailable_error import GatewayUnavailableError
from davos.modules.payments.application.ports.payment_request import PaymentRequest
from davos.modules.payments.application.ports.verification_outcome import VerificationOutcome
from davos.modules.payments.application.ports.verification_request import VerificationRequest
from davos.shared_kernel.domain.money import Money

SANDBOX = "https://sandbox.zarinpal.test"
LIVE = "https://payment.zarinpal.test"
MERCHANT = "12345678-1234-1234-1234-123456789012"
AUTHORITY = "A0000000000000000000000000000000abcd"
REQUEST = PaymentRequest("pay-1", "order-1", Money(250_000), "شرح", "https://davoskarting.ir/cb", 1_000_001)


@pytest.fixture
async def client():
    async with httpx.AsyncClient() as c:
        yield c


def gateway(client: httpx.AsyncClient, *, sandbox: bool = True) -> ZarinpalPaymentGateway:
    return ZarinpalPaymentGateway(
        http_client=client,
        merchant_id=MERCHANT,
        sandbox=sandbox,
        api_host=LIVE,
        sandbox_host=SANDBOX,
        timeout_seconds=5.0,
    )


@respx.mock
async def test_request_sends_integer_rials_with_an_explicit_currency(client: httpx.AsyncClient) -> None:
    route = respx.post(f"{SANDBOX}/pg/v4/payment/request.json").mock(
        return_value=httpx.Response(
            200, json={"data": {"code": 100, "message": "Success", "authority": AUTHORITY}, "errors": []}
        )
    )
    session = await gateway(client).request_payment(REQUEST)
    body = json.loads(route.calls.last.request.content)
    assert body["amount"] == 250_000 and isinstance(body["amount"], int)
    assert body["currency"] == "IRR"  # never rely on the provider default
    assert body["merchant_id"] == MERCHANT and body["callback_url"] == "https://davoskarting.ir/cb"
    assert body["metadata"] == {"order_id": "1000001"}
    assert session.authority == AUTHORITY
    assert session.redirect_url == f"{SANDBOX}/pg/StartPay/{AUTHORITY}"


@respx.mock
async def test_production_mode_uses_the_live_host(client: httpx.AsyncClient) -> None:
    respx.post(f"{LIVE}/pg/v4/payment/request.json").mock(
        return_value=httpx.Response(200, json={"data": {"code": 100, "authority": AUTHORITY}, "errors": []})
    )
    session = await gateway(client, sandbox=False).request_payment(REQUEST)
    assert session.redirect_url.startswith(LIVE)


@respx.mock
async def test_error_shape_from_the_provider_is_a_rejection_with_its_code(client: httpx.AsyncClient) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/request.json").mock(
        return_value=httpx.Response(
            200, json={"data": [], "errors": {"code": -9, "message": "validation", "validations": []}}
        )
    )
    with pytest.raises(GatewayRejectedError) as info:
        await gateway(client).request_payment(REQUEST)
    assert info.value.provider_code == -9


@respx.mock
async def test_success_without_an_authority_is_not_accepted(client: httpx.AsyncClient) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/request.json").mock(
        return_value=httpx.Response(200, json={"data": {"code": 100}, "errors": []})
    )
    with pytest.raises(GatewayRejectedError):
        await gateway(client).request_payment(REQUEST)


@respx.mock
async def test_verify_maps_100_and_101_and_keeps_only_the_reference(client: httpx.AsyncClient) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "code": 100,
                    "message": "Verified",
                    "ref_id": 201,
                    "card_pan": "603799******1234",
                    "card_hash": "abc",
                    "fee": 10,
                },
                "errors": [],
            },
        )
    )
    result = await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(250_000)))
    assert result.outcome is VerificationOutcome.VERIFIED and result.reference_id == "201"
    assert not hasattr(result, "card_pan") and "603799" not in repr(result)  # banking data is discarded

    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(
        return_value=httpx.Response(
            200, json={"data": {"code": 101, "message": "Verified", "ref_id": 201}, "errors": []}
        )
    )
    again = await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(250_000)))
    assert again.outcome is VerificationOutcome.ALREADY_VERIFIED


@respx.mock
async def test_verify_sends_the_stored_amount_and_authority(client: httpx.AsyncClient) -> None:
    route = respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(
        return_value=httpx.Response(200, json={"data": {"code": 100, "ref_id": 1}, "errors": []})
    )
    await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(250_000)))
    assert json.loads(route.calls.last.request.content) == {
        "merchant_id": MERCHANT,
        "amount": 250_000,
        "authority": AUTHORITY,
    }


@respx.mock
@pytest.mark.parametrize("code", [-50, -51, -52, -54, -55])
async def test_definitive_provider_failures_are_rejections_not_errors(client: httpx.AsyncClient, code: int) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(
        return_value=httpx.Response(200, json={"data": [], "errors": {"code": code, "message": "x"}})
    )
    result = await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(250_000)))
    assert result.outcome is VerificationOutcome.REJECTED and result.provider_code == code


@respx.mock
async def test_timeouts_and_outages_are_errors_so_the_caller_records_unknown(client: httpx.AsyncClient) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(GatewayTimeoutError):
        await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(1)))
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(side_effect=httpx.ConnectError("refused"))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(1)))
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(return_value=httpx.Response(502, text="bad gateway"))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(1)))
    respx.post(f"{SANDBOX}/pg/v4/payment/verify.json").mock(return_value=httpx.Response(200, text="<html>"))
    with pytest.raises(GatewayUnavailableError):
        await gateway(client).verify_payment(VerificationRequest(AUTHORITY, Money(1)))


@respx.mock
async def test_the_merchant_id_never_reaches_the_logs(
    client: httpx.AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    respx.post(f"{SANDBOX}/pg/v4/payment/request.json").mock(return_value=httpx.Response(500))
    with caplog.at_level(logging.DEBUG), pytest.raises(GatewayUnavailableError) as info:
        await gateway(client).request_payment(REQUEST)
    assert MERCHANT not in caplog.text + str(info.value)
