"""Per-person access to the admin panel's sections: enforced by the server, effective at once, owner-only to change."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import httpx
import pytest

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway
from tests.integration.api.conftest import ORIGIN

pytestmark = pytest.mark.integration

OWNER_PASSWORD = "Owner-password-2026"
STAFF_PASSWORD = "Staff-password-2026"


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 3, 6, 0, tzinfo=UTC))


@pytest.fixture
def container(test_settings: AppSettings, engine, clock: FixedClock) -> ApplicationContainer:
    settings = test_settings.model_copy(
        update={"admin_bootstrap_username": "owner", "admin_bootstrap_password": OWNER_PASSWORD}
    )
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        redis=None,
        clock=clock,
        rate_limiter=InMemoryRateLimiter(clock),
        sms_gateway=RecordingSmsGateway(),
        ai_chat=ScriptedAiChat("x"),
        ai_budget=InMemoryAiBudget(daily_limit=1_000_000, clock=clock),
        payment_gateway=ScriptedPaymentGateway(),
    )


@pytest.fixture
async def owner_api(container: ApplicationContainer) -> AsyncIterator[httpx.AsyncClient]:
    await container.manage_admins().ensure_bootstrap_owner(username="owner", password=OWNER_PASSWORD)
    transport = httpx.ASGITransport(
        app=create_app(container.settings, container), client=("203.0.113.9", 1), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
async def staff_api(container: ApplicationContainer) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(
        app=create_app(container.settings, container), client=("203.0.113.10", 1), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def login(client: httpx.AsyncClient, username: str, password: str) -> dict[str, str]:
    response = await client.post("/api/v1/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"], "Origin": ORIGIN}


async def add_staff(owner: httpx.AsyncClient, headers: dict[str, str], **extra: object) -> str:
    created = await owner.post(
        "/api/v1/admin/users",
        json={"username": "reza", "display_name": "رضا", "password": STAFF_PASSWORD, "role": "staff", **extra},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    return created.json()["admin_id"]


async def status(client: httpx.AsyncClient, path: str, headers: dict[str, str]) -> int:
    return (await client.get(f"/api/v1/admin{path}", headers=headers)).status_code


async def test_a_new_staff_account_keeps_what_staff_could_always_do_and_nothing_more(
    owner_api: httpx.AsyncClient, staff_api: httpx.AsyncClient
) -> None:
    owner = await login(owner_api, "owner", OWNER_PASSWORD)
    await add_staff(owner_api, owner)
    staff = await login(staff_api, "reza", STAFF_PASSWORD)
    for path in (
        "/dashboard",
        "/payments",
        "/customers",
        "/settings/schedule",
        "/system/status",
        "/assistant/overview",
        "/sms/messages",
    ):
        assert await status(staff_api, path, staff) == 200, path
    for path in ("/accounting/accounts", "/accounting/reports/dashboard", "/users"):
        assert await status(staff_api, path, staff) == 403, path
    settings = (await staff_api.get("/api/v1/admin/settings/schedule")).json()
    changed = await staff_api.put("/api/v1/admin/settings/schedule", json=settings, headers=staff)
    assert changed.status_code == 403 and changed.json()["code"] == "permission_denied"


async def test_the_owner_chooses_exactly_what_a_person_can_open_and_it_applies_to_the_next_request(
    owner_api: httpx.AsyncClient, staff_api: httpx.AsyncClient
) -> None:
    owner = await login(owner_api, "owner", OWNER_PASSWORD)
    admin_id = await add_staff(owner_api, owner)
    staff = await login(staff_api, "reza", STAFF_PASSWORD)  # one session, kept through every change below
    assert await status(staff_api, "/payments", staff) == 200
    restricted = await owner_api.put(
        f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": ["reservations"]}, headers=owner
    )
    assert restricted.status_code == 200 and restricted.json()["permissions"] == ["reservations"]
    assert restricted.json()["custom_permissions"] is True
    assert await status(staff_api, "/payments", staff) == 403
    denied = await staff_api.get("/api/v1/admin/payments")
    assert denied.json()["code"] == "permission_denied" and "اجازه" in denied.json()["message"]
    assert await status(staff_api, "/reservations/board?date=2026-01-04", staff) == 200
    me = (await staff_api.get("/api/v1/admin/auth/me")).json()
    assert me["permissions"] == ["reservations"] and me["role"] == "staff"

    await owner_api.put(
        f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": ["accounting"]}, headers=owner
    )
    assert await status(staff_api, "/accounting/accounts", staff) == 200
    assert await status(staff_api, "/reservations/board?date=2026-01-04", staff) == 403

    await owner_api.put(
        f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": ["settings.manage"]}, headers=owner
    )
    assert await status(staff_api, "/settings/schedule", staff) == 200  # managing includes looking
    settings = (await staff_api.get("/api/v1/admin/settings/schedule")).json()
    assert (await staff_api.put("/api/v1/admin/settings/schedule", json=settings, headers=staff)).status_code == 200

    back = await owner_api.put(f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": None}, headers=owner)
    assert back.json()["custom_permissions"] is False and "payments" in back.json()["permissions"]


async def test_nobody_but_the_owner_can_change_permissions_and_the_owner_cannot_be_restricted(
    owner_api: httpx.AsyncClient, staff_api: httpx.AsyncClient
) -> None:
    owner = await login(owner_api, "owner", OWNER_PASSWORD)
    admin_id = await add_staff(owner_api, owner, permissions=["dashboard"])
    staff = await login(staff_api, "reza", STAFF_PASSWORD)
    assert (
        await staff_api.put(
            f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": ["accounting"]}, headers=staff
        )
    ).status_code == 403
    assert await status(staff_api, "/users/catalog", staff) == 403
    users = (await owner_api.get("/api/v1/admin/users")).json()
    owner_id = next(u["admin_id"] for u in users if u["role"] == "owner")
    assert (
        await owner_api.put(f"/api/v1/admin/users/{owner_id}/permissions", json={"permissions": ["sms"]}, headers=owner)
    ).status_code == 409
    assert (
        await owner_api.put(
            f"/api/v1/admin/users/{admin_id}/permissions", json={"permissions": ["users"]}, headers=owner
        )
    ).status_code == 422
    owner_me = (await owner_api.get("/api/v1/admin/auth/me")).json()
    assert "accounting" in owner_me["permissions"] and "settings.manage" in owner_me["permissions"]
    created = next(u for u in users if u["admin_id"] == admin_id)
    assert created["permissions"] == ["dashboard"]


async def test_the_catalog_lists_every_permission_and_the_presets(owner_api: httpx.AsyncClient) -> None:
    owner = await login(owner_api, "owner", OWNER_PASSWORD)
    catalog = (await owner_api.get("/api/v1/admin/users/catalog", headers=owner)).json()
    keys = {e["key"] for e in catalog["entries"]}
    assert {"accounting", "settings", "settings.manage", "assistant.manage"} <= keys
    assert {p["key"] for p in catalog["presets"]} >= {"reception", "accountant"}
    assert next(e for e in catalog["entries"] if e["key"] == "settings.manage")["implies"] == "settings"
