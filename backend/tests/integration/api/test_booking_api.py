from __future__ import annotations

import uuid

import httpx
import pytest

from davos.composition.application_container import ApplicationContainer
from tests.integration.api.conftest import SignedInCustomer
from tests.support.booking_webhooks import encode, payload, sign

pytestmark = pytest.mark.integration
URL = "/api/v1/integrations/booking/webhook"


def signed(container: ApplicationContainer, data: dict[str, object], **kw: int) -> tuple[bytes, dict[str, str]]:
    body = encode(data)
    ts = int(container.clock.now().timestamp()) + kw.get("offset", 0)
    return body, {"X-Davos-Signature": sign(body, timestamp=ts), "Content-Type": "application/json"}


async def test_a_signed_webhook_is_accepted_and_a_repeat_is_reported_as_duplicate(
    api: httpx.AsyncClient, container: ApplicationContainer, sign_in_as
) -> None:
    customer: SignedInCustomer = await sign_in_as()
    body, headers = signed(container, payload(uuid.UUID(customer.user_id)))
    first = await api.post(URL, content=body, headers=headers)
    again = await api.post(URL, content=body, headers=headers)
    assert (first.status_code, first.json()) == (202, {"outcome": "accepted"})
    assert again.json() == {"outcome": "duplicate"}


async def test_unsigned_tampered_and_replayed_webhooks_are_401_with_a_generic_message(
    api: httpx.AsyncClient, container: ApplicationContainer
) -> None:
    data = payload(uuid.uuid4())
    body, headers = signed(container, data)
    for request in (
        {"content": body, "headers": {"Content-Type": "application/json"}},  # no signature at all
        {"content": body.replace(b"confirmed", b"refunded"), "headers": headers},  # tampered
        {
            "content": signed(container, data, offset=-3600)[0],
            "headers": signed(container, data, offset=-3600)[1],
        },  # replay
    ):
        response = await api.post(URL, **request)
        assert response.status_code == 401
        assert response.json()["code"] == "webhook_signature_invalid" and "mismatch" not in response.text


async def test_oversized_payloads_are_refused_before_any_processing(api: httpx.AsyncClient) -> None:
    response = await api.post(URL, content=b"x" * 70_000, headers={"X-Davos-Signature": "t=1,v1=00"})
    assert response.status_code == 413 and response.json()["code"] == "payload_too_large"


async def test_the_webhook_is_hidden_while_the_integration_is_disabled(
    container: ApplicationContainer, test_settings
) -> None:
    from davos.api.app_factory import create_app

    disabled_settings = test_settings.model_copy(update={"booking_integration_enabled": False})
    disabled = ApplicationContainer(
        settings=disabled_settings,
        engine=container.engine,
        redis=None,
        clock=container.clock,
        rate_limiter=container.rate_limiter,
        sms_gateway=container.sms_gateway,
        ai_chat=container.ai_chat,
        ai_budget=container.ai_budget,
        payment_gateway=container.payment_gateway,
        order_quotes=container.order_quotes,
    )
    transport = httpx.ASGITransport(app=create_app(disabled_settings, disabled))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(URL, content=b"{}", headers={"X-Davos-Signature": "t=1,v1=00"})
    assert response.status_code == 404 and response.json()["code"] == "booking_integration_disabled"


async def test_the_return_page_is_pending_until_the_verified_webhook_arrives(
    api: httpx.AsyncClient, container: ApplicationContainer, sign_in_as
) -> None:
    customer = await sign_in_as()
    forged = await api.get("/api/v1/bookings/return", params={"booking": "bk-1", "status": "success", "paid": "true"})
    assert forged.json() == {
        "state": "pending_confirmation",
        "message": "در انتظار تایید",
        "session_time": None,
        "amount_irr": None,
    }

    body, headers = signed(container, payload(uuid.UUID(customer.user_id)))
    await api.post(URL, content=body, headers=headers)
    confirmed = (await api.get("/api/v1/bookings/return", params={"booking": "bk-1"})).json()
    assert confirmed["state"] == "confirmed" and confirmed["amount_irr"] == 500_000


async def test_the_return_page_requires_a_signed_in_customer(api: httpx.AsyncClient) -> None:
    assert (await api.get("/api/v1/bookings/return", params={"booking": "bk-1"})).status_code == 401
