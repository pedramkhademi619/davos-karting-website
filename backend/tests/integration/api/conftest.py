from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.platform.settings.app_settings import AppSettings

CLIENT_IP = "203.0.113.5"
ORIGIN = "http://localhost:3000"


@pytest.fixture
async def api(container: ApplicationContainer, test_settings: AppSettings) -> AsyncIterator[httpx.AsyncClient]:
    app = create_app(test_settings, container)
    transport = httpx.ASGITransport(app=app, client=(CLIENT_IP, 50000), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


class SignedInCustomer:
    def __init__(self, client: httpx.AsyncClient, csrf_token: str, user_id: str, cookie: str) -> None:
        self.client = client
        self.csrf_token = csrf_token
        self.user_id = user_id
        self.cookie = cookie

    @property
    def headers(self) -> dict[str, str]:
        return {"X-CSRF-Token": self.csrf_token, "Origin": ORIGIN}


async def sign_in(
    client: httpx.AsyncClient, gateway: RecordingSmsGateway, mobile: str = "09123456789"
) -> SignedInCustomer:
    sent_before = len(gateway.sent)
    requested = await client.post("/api/v1/auth/otp/request", json={"mobile": mobile})
    assert requested.status_code == 200, requested.text
    assert len(gateway.sent) == sent_before + 1
    code = gateway.sent[-1].parameters["code"]
    verified = await client.post("/api/v1/auth/otp/verify", json={"mobile": mobile, "code": code})
    assert verified.status_code == 200, verified.text
    body = verified.json()
    return SignedInCustomer(client, body["csrf_token"], body["user_id"], client.cookies["davos_session"])


@pytest.fixture
def sign_in_as(api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway):
    async def _sign_in(mobile: str = "09123456789") -> SignedInCustomer:
        return await sign_in(api, sms_gateway, mobile)

    return _sign_in
