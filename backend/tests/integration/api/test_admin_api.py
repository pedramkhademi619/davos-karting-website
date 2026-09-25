"""The admin panel API: staff sign-in and roles, reservations, settings, customers and SMS."""

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
from tests.integration.api.conftest import ORIGIN, sign_in

pytestmark = pytest.mark.integration

OWNER_PASSWORD = "Owner-password-2026"
STAFF_PASSWORD = "Staff-password-2026"


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 1, 3, 6, 0, tzinfo=UTC))


@pytest.fixture
def container(
    test_settings: AppSettings, engine, clock: FixedClock, sms_gateway: RecordingSmsGateway
) -> ApplicationContainer:
    settings = test_settings.model_copy(
        update={"admin_bootstrap_username": "owner", "admin_bootstrap_password": OWNER_PASSWORD}
    )
    return ApplicationContainer(
        settings=settings,
        engine=engine,
        redis=None,
        clock=clock,
        rate_limiter=InMemoryRateLimiter(clock),
        sms_gateway=sms_gateway,
        ai_chat=ScriptedAiChat("پاسخ [1]"),
        ai_budget=InMemoryAiBudget(daily_limit=1_000_000, clock=clock),
        payment_gateway=ScriptedPaymentGateway(),
    )


@pytest.fixture
async def admin_api(container: ApplicationContainer) -> AsyncIterator[httpx.AsyncClient]:
    await container.manage_admins().ensure_bootstrap_owner(username="owner", password=OWNER_PASSWORD)
    transport = httpx.ASGITransport(
        app=create_app(container.settings, container), client=("203.0.113.9", 1), raise_app_exceptions=False
    )
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


async def login(client: httpx.AsyncClient, username: str = "owner", password: str = OWNER_PASSWORD) -> dict[str, str]:
    response = await client.post("/api/v1/admin/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"X-CSRF-Token": response.json()["csrf_token"], "Origin": ORIGIN}


async def test_everything_under_admin_needs_a_staff_session(admin_api: httpx.AsyncClient) -> None:
    for path in (
        "/api/v1/admin/dashboard",
        "/api/v1/admin/reservations",
        "/api/v1/admin/settings/schedule",
        "/api/v1/admin/customers",
        "/api/v1/admin/payments",
        "/api/v1/admin/sms/messages",
    ):
        assert (await admin_api.get(path)).status_code == 401, path


async def test_a_customer_session_is_not_a_staff_session(
    admin_api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    customer = await sign_in(admin_api, sms_gateway)
    assert (await admin_api.get("/api/v1/admin/dashboard", headers=customer.headers)).status_code == 401


async def test_sign_in_sets_a_strict_cookie_scoped_to_the_admin_api(admin_api: httpx.AsyncClient) -> None:
    response = await admin_api.post("/api/v1/admin/auth/login", json={"username": "OWNER", "password": OWNER_PASSWORD})
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie and "path=/api/v1/admin" in cookie
    me = (await admin_api.get("/api/v1/admin/auth/me")).json()
    assert me["username"] == "owner" and me["role"] == "owner"


async def test_wrong_passwords_get_one_generic_answer_and_then_lock_the_account(admin_api: httpx.AsyncClient) -> None:
    unknown = await admin_api.post("/api/v1/admin/auth/login", json={"username": "nobody", "password": "x"})
    assert unknown.status_code == 401 and unknown.json()["code"] == "admin_login_failed"
    for _ in range(5):
        wrong = await admin_api.post("/api/v1/admin/auth/login", json={"username": "owner", "password": "wrong-one"})
        assert wrong.status_code == 401 and wrong.json()["message"] == unknown.json()["message"]
    locked = await admin_api.post("/api/v1/admin/auth/login", json={"username": "owner", "password": OWNER_PASSWORD})
    assert locked.status_code == 429 and locked.json()["code"] == "admin_locked"


async def test_state_changes_need_the_csrf_token(admin_api: httpx.AsyncClient) -> None:
    await login(admin_api)
    response = await admin_api.post(
        "/api/v1/admin/sms/send", json={"audience": "numbers", "numbers": ["09120000000"], "text": "سلام"}
    )
    assert response.status_code == 403


async def test_logout_ends_the_session(admin_api: httpx.AsyncClient) -> None:
    headers = await login(admin_api)
    assert (await admin_api.post("/api/v1/admin/auth/logout", headers=headers)).status_code == 204
    assert (await admin_api.get("/api/v1/admin/auth/me")).status_code == 401


async def test_the_owner_edits_prices_and_capacity_and_the_site_follows(admin_api: httpx.AsyncClient) -> None:
    headers = await login(admin_api)
    settings = (await admin_api.get("/api/v1/admin/settings/schedule")).json()
    assert settings["normal_single_toman"] == 790_000 and settings["closed_weekdays"] == [3, 4]
    settings.update(normal_single_toman=850_000, single_capacity=4, max_days_ahead=2)
    saved = await admin_api.put("/api/v1/admin/settings/schedule", json=settings, headers=headers)
    assert saved.status_code == 200, saved.text
    calendar = (await admin_api.get("/api/v1/reservations/calendar")).json()
    assert calendar["days"][0]["single_price_toman"] == 850_000 and len(calendar["days"]) == 2
    day = (await admin_api.get("/api/v1/reservations/availability", params={"date": "2026-01-04"})).json()
    assert day["sessions"][0]["single_capacity"] == 4
    info = (await admin_api.get("/api/v1/reservations/info")).json()  # public: home page, FAQ and assistant follow
    assert info["single_capacity"] == 4 and info["double_capacity"] == 1
    assert info["normal_single_toman"] == 850_000 and info["max_days_ahead"] == 2
    assert info["closed_weekdays"] == ["پنجشنبه", "جمعه"] and info["first_session"] == "15:00"

    settings["interval_minutes"] = 1
    bad = await admin_api.put("/api/v1/admin/settings/schedule", json=settings, headers=headers)
    assert bad.status_code == 422 and bad.json()["code"] == "invalid_schedule_settings"


async def test_staff_run_the_day_but_only_the_owner_changes_settings_and_accounts(admin_api: httpx.AsyncClient) -> None:
    owner = await login(admin_api)
    created = await admin_api.post(
        "/api/v1/admin/users",
        json={"username": "reza", "display_name": "رضا", "password": STAFF_PASSWORD, "role": "staff"},
        headers=owner,
    )
    assert created.status_code == 201
    weak = await admin_api.post(
        "/api/v1/admin/users", json={"username": "ali", "password": "short", "role": "staff"}, headers=owner
    )
    assert weak.status_code == 422

    admin_api.cookies.clear()
    staff = await login(admin_api, "reza", STAFF_PASSWORD)
    settings = (await admin_api.get("/api/v1/admin/settings/schedule")).json()
    assert (await admin_api.put("/api/v1/admin/settings/schedule", json=settings, headers=staff)).status_code == 403
    assert (await admin_api.get("/api/v1/admin/users")).status_code == 403
    entry = await admin_api.post(
        "/api/v1/admin/reservations",
        json={"date": "2026-01-04", "time": "20:00", "single_count": 6, "double_count": 1, "note": "تولد"},
        headers=staff,
    )
    assert entry.status_code == 201 and entry.json()["source"] == "staff" and entry.json()["status"] == "confirmed"
    board = (await admin_api.get("/api/v1/admin/reservations/board", params={"date": "2026-01-04"})).json()
    eight = next(s for s in board["sessions"] if s["time"] == "20:00")
    assert (eight["singles_left"], eight["doubles_left"]) == (0, 0)

    found = (await admin_api.get("/api/v1/admin/reservations", params={"q": entry.json()["code"]})).json()
    assert found["total"] == 1
    checked_in = await admin_api.post(f"/api/v1/admin/reservations/{entry.json()['id']}/attended", headers=staff)
    assert checked_in.json()["status"] == "attended"


async def test_staff_send_sms_to_typed_numbers_and_see_the_log(
    admin_api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    headers = await login(admin_api)
    sent = await admin_api.post(
        "/api/v1/admin/sms/send",
        json={
            "audience": "numbers",
            "numbers": ["0912 000 0001", "+989120000002", "123", "09120000001"],
            "text": "پیست فردا از ساعت ۱۶ باز است.",
        },
        headers=headers,
    )
    assert sent.status_code == 200, sent.text
    report = sent.json()
    assert report["accepted"] == 2 and report["invalid_numbers"] == ["123"]
    assert sms_gateway.texts[-1][0] == ["09120000001", "09120000002"]
    log = (await admin_api.get("/api/v1/admin/sms/messages")).json()
    assert log["total"] == 2 and {m["recipient"] for m in log["items"]} == {"09120000001", "09120000002"}
    account = (await admin_api.get("/api/v1/admin/sms/account")).json()
    assert account == {"provider": "recording", "connected": False, "remaining_credit_toman": None, "expires_at": None}


async def test_news_goes_only_to_customers_who_agreed(
    admin_api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    yes = await sign_in(admin_api, sms_gateway, "09121111111")
    await admin_api.put(
        "/api/v1/account/profile", json={"full_name": "نگار", "marketing_opt_in": True}, headers=yes.headers
    )
    admin_api.cookies.clear()
    await sign_in(admin_api, sms_gateway, "09122222222")  # never agreed
    admin_api.cookies.clear()
    headers = await login(admin_api)
    sent = await admin_api.post(
        "/api/v1/admin/sms/send", json={"audience": "subscribers", "text": "تخفیف ویژه آخر هفته"}, headers=headers
    )
    assert sent.json()["accepted"] == 1 and sms_gateway.texts[-1][0] == ["09121111111"]
    customers = (await admin_api.get("/api/v1/admin/customers", params={"q": "نگار"})).json()
    assert customers["total"] == 1 and customers["items"][0]["mobile"] == "09121111111"


async def test_a_blocked_customer_cannot_sign_in(
    admin_api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    customer = await sign_in(admin_api, sms_gateway, "09123333333")
    admin_api.cookies.clear()
    headers = await login(admin_api)
    blocked = await admin_api.post(
        f"/api/v1/admin/customers/{customer.user_id}/status", json={"status": "blocked"}, headers=headers
    )
    assert blocked.json()["status"] == "blocked"
    admin_api.cookies.clear()
    admin_api.cookies.set("davos_session", customer.cookie)
    assert (await admin_api.get("/api/v1/account/profile")).status_code == 401


async def test_the_dashboard_summarises_today(admin_api: httpx.AsyncClient) -> None:
    await login(admin_api)
    dashboard = (await admin_api.get("/api/v1/admin/dashboard")).json()
    assert dashboard["online_booking_enabled"] is True and dashboard["today_confirmed"] == 0
