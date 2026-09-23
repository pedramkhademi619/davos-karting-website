from __future__ import annotations

import uuid

import httpx
import pytest

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from tests.fakes.fixed_order_quotes import FixedOrderQuotes
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway
from tests.integration.api.conftest import SignedInCustomer, sign_in

pytestmark = pytest.mark.integration


async def start(api: httpx.AsyncClient, customer: SignedInCustomer, order: str = "order-1"):
    return await api.post("/api/v1/payments", json={"order_ref": order}, headers=customer.headers)


async def test_full_sandbox_style_flow_through_the_api(
    api: httpx.AsyncClient, sign_in_as, quotes: FixedOrderQuotes, gateway: ScriptedPaymentGateway
) -> None:
    customer = await sign_in_as()
    quotes.add("order-1", uuid.UUID(customer.user_id), 250_000)

    started = await start(api, customer)
    assert started.status_code == 200
    assert started.json()["redirect_url"].endswith(gateway.authority)

    back = await api.get("/api/v1/payments/callback", params={"Authority": gateway.authority, "Status": "OK"})
    assert back.json()["status"] == "paid"

    detail = (await api.get(f"/api/v1/payments/{started.json()['payment_id']}")).json()
    assert (detail["status"], detail["amount_irr"], detail["amount_toman"], detail["reference_id"]) == (
        "paid",
        250_000,
        25_000,
        "777",
    )


async def test_the_request_cannot_carry_a_price(api: httpx.AsyncClient, sign_in_as) -> None:
    customer = await sign_in_as()
    response = await api.post("/api/v1/payments", json={"order_ref": "order-1", "amount": 1}, headers=customer.headers)
    assert response.status_code == 422


async def test_starting_a_payment_requires_csrf_and_a_session(api: httpx.AsyncClient, sign_in_as) -> None:
    assert (await api.post("/api/v1/payments", json={"order_ref": "order-1"})).status_code == 401
    await sign_in_as()
    assert (await api.post("/api/v1/payments", json={"order_ref": "order-1"})).status_code == 403


async def test_unknown_and_foreign_orders_are_404(api: httpx.AsyncClient, sign_in_as, quotes: FixedOrderQuotes) -> None:
    customer = await sign_in_as()
    quotes.add("theirs", uuid.uuid4(), 100_000)
    assert (await start(api, customer, "theirs")).status_code == 404
    assert (await start(api, customer, "nothing")).status_code == 404


async def test_refreshing_the_callback_does_not_pay_twice(
    api: httpx.AsyncClient, sign_in_as, quotes: FixedOrderQuotes, gateway: ScriptedPaymentGateway
) -> None:
    customer = await sign_in_as()
    quotes.add("order-1", uuid.UUID(customer.user_id), 250_000)
    await start(api, customer)
    for _ in range(3):
        response = await api.get("/api/v1/payments/callback", params={"Authority": gateway.authority, "Status": "OK"})
        assert response.json()["status"] == "paid"
    assert len(gateway.verifications) == 1


async def test_another_customer_cannot_verify_or_view_the_payment(
    api: httpx.AsyncClient, sign_in_as, quotes: FixedOrderQuotes, gateway: ScriptedPaymentGateway
) -> None:
    owner = await sign_in_as("09123456789")
    quotes.add("order-1", uuid.UUID(owner.user_id), 250_000)
    payment_id = (await start(api, owner)).json()["payment_id"]
    api.cookies.clear()

    await sign_in_as("09129999999")
    assert (
        await api.get("/api/v1/payments/callback", params={"Authority": gateway.authority, "Status": "OK"})
    ).status_code == 404
    assert (await api.get(f"/api/v1/payments/{payment_id}")).status_code == 404
    assert (await api.get("/api/v1/payments/not-a-uuid")).status_code == 404
    assert gateway.verifications == []


async def test_a_cancelled_payment_reports_failed_without_asking_the_provider(
    api: httpx.AsyncClient, sign_in_as, quotes: FixedOrderQuotes, gateway: ScriptedPaymentGateway
) -> None:
    customer = await sign_in_as()
    quotes.add("order-1", uuid.UUID(customer.user_id), 250_000)
    await start(api, customer)
    response = await api.get("/api/v1/payments/callback", params={"Authority": gateway.authority, "Status": "NOK"})
    assert response.json()["status"] == "failed" and gateway.verifications == []


async def test_payments_are_hidden_while_the_feature_flag_is_off(
    container: ApplicationContainer, test_settings, sms_gateway
) -> None:
    settings = test_settings.model_copy(update={"payments_enabled": False})
    off = ApplicationContainer(
        settings=settings,
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
    transport = httpx.ASGITransport(app=create_app(settings, off), client=("203.0.113.5", 1))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        customer = await sign_in(client, sms_gateway)
        response = await client.post("/api/v1/payments", json={"order_ref": "order-1"}, headers=customer.headers)
        callback = await client.get("/api/v1/payments/callback", params={"Authority": "A1", "Status": "OK"})
    assert response.status_code == 404 and response.json()["code"] == "payments_disabled"
    assert callback.status_code == 404
