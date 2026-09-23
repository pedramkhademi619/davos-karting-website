from __future__ import annotations

import httpx
import pytest

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.platform.settings.app_settings import AppSettings
from tests.integration.api.conftest import CLIENT_IP, ORIGIN

pytestmark = pytest.mark.integration


async def test_request_otp_sends_an_sms_and_never_returns_the_code(
    api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    response = await api.post("/api/v1/auth/otp/request", json={"mobile": "۰۹۱۲۳۴۵۶۷۸۹"})
    assert response.status_code == 200
    assert response.json() == {"expires_in_seconds": 120, "resend_after_seconds": 60}
    code = sms_gateway.sent[-1].parameters["code"]
    assert code not in response.text
    assert sms_gateway.sent[-1].to_local_mobile == "09123456789"


async def test_invalid_mobile_uses_the_uniform_error_format(api: httpx.AsyncClient) -> None:
    response = await api.post("/api/v1/auth/otp/request", json={"mobile": "12345678901"})
    body = response.json()
    assert response.status_code == 422
    assert set(body) == {"code", "message", "details", "request_id"}
    assert body["code"] == "invalid_mobile_number"
    assert body["request_id"] == response.headers["x-request-id"]


async def test_request_validation_errors_list_the_offending_fields(api: httpx.AsyncClient) -> None:
    response = await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789", "admin": True})
    body = response.json()
    assert response.status_code == 422 and body["code"] == "validation_error"
    assert any("admin" in d["field"] for d in body["details"])


async def test_sign_in_sets_a_hardened_session_cookie(api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway) -> None:
    await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
    code = sms_gateway.sent[-1].parameters["code"]
    response = await api.post("/api/v1/auth/otp/verify", json={"mobile": "09123456789", "code": code})

    assert response.status_code == 200
    body = response.json()
    cookie = response.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    session_token = api.cookies["davos_session"]
    assert session_token not in response.text  # the bearer token never appears in the body
    assert body["is_new_user"] is True and body["csrf_token"]


async def test_session_cookie_is_secure_when_configured(
    container: ApplicationContainer, test_settings: AppSettings, sms_gateway: RecordingSmsGateway
) -> None:
    settings = test_settings.model_copy(update={"cookie_secure": True})
    secure_container = ApplicationContainer(
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
    app = create_app(settings, secure_container)
    transport = httpx.ASGITransport(app=app, client=(CLIENT_IP, 1))
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        await client.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
        code = sms_gateway.sent[-1].parameters["code"]
        response = await client.post("/api/v1/auth/otp/verify", json={"mobile": "09123456789", "code": code})
    assert "Secure" in response.headers["set-cookie"]


async def test_persian_digits_in_the_code_are_accepted(
    api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
    code = sms_gateway.sent[-1].parameters["code"]
    persian = code.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    response = await api.post("/api/v1/auth/otp/verify", json={"mobile": "09123456789", "code": persian})
    assert response.status_code == 200


async def test_wrong_code_is_401_with_a_generic_message(
    api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway
) -> None:
    await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
    response = await api.post("/api/v1/auth/otp/verify", json={"mobile": "09123456789", "code": "000000"})
    assert response.status_code == 401
    assert response.json()["code"] == "otp_verification_failed"
    assert "davos_session" not in api.cookies


async def test_me_requires_authentication(api: httpx.AsyncClient) -> None:
    response = await api.get("/api/v1/auth/me")
    assert response.status_code == 401 and response.json()["code"] == "unauthenticated"


async def test_a_tampered_cookie_is_rejected(api: httpx.AsyncClient, sign_in_as) -> None:
    await sign_in_as()
    api.cookies.set("davos_session", "not-the-real-token")
    assert (await api.get("/api/v1/auth/me")).status_code == 401


async def test_me_returns_the_customer_and_csrf_token(api: httpx.AsyncClient, sign_in_as) -> None:
    customer = await sign_in_as()
    body = (await api.get("/api/v1/auth/me")).json()
    assert body == {"user_id": customer.user_id, "csrf_token": customer.csrf_token}


async def test_state_changing_requests_need_a_valid_csrf_token(api: httpx.AsyncClient, sign_in_as) -> None:
    customer = await sign_in_as()
    assert (await api.post("/api/v1/auth/logout")).status_code == 403
    assert (await api.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "forged"})).status_code == 403
    assert (await api.get("/api/v1/auth/me")).status_code == 200  # still signed in after the refusals
    assert (await api.post("/api/v1/auth/logout", headers=customer.headers)).status_code == 204


async def test_requests_from_foreign_origins_are_refused_even_with_a_valid_token(
    api: httpx.AsyncClient, sign_in_as
) -> None:
    customer = await sign_in_as()
    headers = {"X-CSRF-Token": customer.csrf_token, "Origin": "https://evil.example"}
    assert (await api.post("/api/v1/auth/logout", headers=headers)).status_code == 403


async def test_csrf_token_of_another_session_does_not_work(
    api: httpx.AsyncClient, container, sms_gateway, sign_in_as
) -> None:
    mine = await sign_in_as("09123456789")
    other_client = httpx.AsyncClient(
        transport=httpx.ASGITransport(app=api._transport.app, client=(CLIENT_IP, 2)), base_url="http://testserver"
    )
    async with other_client:
        from tests.integration.api.conftest import sign_in

        theirs = await sign_in(other_client, sms_gateway, "09129999999")
        response = await other_client.post(
            "/api/v1/auth/logout", headers={"X-CSRF-Token": mine.csrf_token, "Origin": ORIGIN}
        )
        assert response.status_code == 403
        assert theirs.csrf_token != mine.csrf_token


async def test_logout_revokes_the_session_and_clears_the_cookie(api: httpx.AsyncClient, sign_in_as) -> None:
    customer = await sign_in_as()
    response = await api.post("/api/v1/auth/logout", headers=customer.headers)
    assert response.status_code == 204
    assert "davos_session=" in response.headers["set-cookie"] and "Max-Age=0" in response.headers["set-cookie"]
    api.cookies.set("davos_session", customer.cookie)  # replaying the old cookie must fail
    assert (await api.get("/api/v1/auth/me")).status_code == 401


async def test_sessions_list_marks_the_current_device(api: httpx.AsyncClient, sign_in_as) -> None:
    await sign_in_as()
    sessions = (await api.get("/api/v1/auth/sessions")).json()
    assert len(sessions) == 1 and sessions[0]["is_current"] is True
    assert sessions[0]["ip_hint"] == "203.0.113.0/24"


async def test_a_customer_cannot_sign_out_someone_elses_device(api: httpx.AsyncClient, sms_gateway, sign_in_as) -> None:
    victim = await sign_in_as("09129999999")
    victim_sessions = (await api.get("/api/v1/auth/sessions")).json()
    victim_session_id = victim_sessions[0]["session_id"]
    api.cookies.clear()

    attacker = await sign_in_as("09120000000")
    response = await api.delete(f"/api/v1/auth/sessions/{victim_session_id}", headers=attacker.headers)
    assert response.status_code == 404  # indistinguishable from a non-existent session

    api.cookies.set("davos_session", victim.cookie)
    assert (await api.get("/api/v1/auth/me")).status_code == 200  # victim is untouched


async def test_malformed_session_ids_are_not_found(api: httpx.AsyncClient, sign_in_as) -> None:
    customer = await sign_in_as()
    response = await api.delete("/api/v1/auth/sessions/not-a-uuid", headers=customer.headers)
    assert response.status_code == 404


async def test_resending_inside_the_cooldown_returns_429_with_retry_after(api: httpx.AsyncClient) -> None:
    assert (await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})).status_code == 200
    response = await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
    assert response.status_code == 429
    assert 0 < int(response.headers["retry-after"]) <= 61
    assert response.json()["code"] == "rate_limited"


async def test_sms_provider_outage_is_reported_as_503(
    api: httpx.AsyncClient, sms_gateway: RecordingSmsGateway, monkeypatch
) -> None:
    from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError

    async def broken(message):
        raise SmsProviderError("provider down", retryable=True)

    monkeypatch.setattr(sms_gateway, "send", broken)
    response = await api.post("/api/v1/auth/otp/request", json={"mobile": "09123456789"})
    assert response.status_code == 503 and response.json()["code"] == "otp_delivery_failed"
    assert "provider down" not in response.text
