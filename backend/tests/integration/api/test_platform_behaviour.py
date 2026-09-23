from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from davos.api.app_factory import create_app
from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.app_settings import AppSettings
from tests.integration.api.conftest import CLIENT_IP, ORIGIN

pytestmark = pytest.mark.integration


async def test_liveness_and_readiness(api: httpx.AsyncClient) -> None:
    assert (await api.get("/api/v1/health/live")).json() == {"status": "ok"}
    ready = await api.get("/api/v1/health/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "checks": {"database": True, "redis": True, "persian_search": True}}


async def test_readiness_reports_a_broken_database_with_503(
    container: ApplicationContainer, test_settings: AppSettings
) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    broken = ApplicationContainer(
        settings=test_settings,
        engine=create_async_engine("postgresql+asyncpg://nobody:nobody@127.0.0.1:1/none"),
        redis=None,
        clock=container.clock,
        rate_limiter=container.rate_limiter,
        sms_gateway=container.sms_gateway,
        ai_chat=container.ai_chat,
        ai_budget=container.ai_budget,
        payment_gateway=container.payment_gateway,
        order_quotes=container.order_quotes,
    )
    transport = httpx.ASGITransport(app=create_app(test_settings, broken))
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health/ready")
    assert response.status_code == 503 and response.json()["status"] == "degraded"
    assert response.json()["checks"]["database"] is False


async def test_every_response_carries_security_headers_and_a_request_id(api: httpx.AsyncClient) -> None:
    response = await api.get("/api/v1/health/live", headers={"X-Request-ID": "trace-1234567890"})
    assert response.headers["x-request-id"] == "trace-1234567890"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-security-policy"].startswith("default-src 'none'")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["referrer-policy"] == "no-referrer"


async def test_unsafe_request_ids_are_replaced(api: httpx.AsyncClient) -> None:
    response = await api.get("/api/v1/health/live", headers={"X-Request-ID": "x\r\nInjected: 1"})
    assert "injected" not in {k.lower() for k in response.headers}
    assert len(response.headers["x-request-id"]) == 32


async def test_unknown_routes_use_the_uniform_error_format(api: httpx.AsyncClient) -> None:
    response = await api.get("/api/v1/nothing-here")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "message", "details", "request_id"}


async def test_unhandled_errors_never_leak_internals(
    container: ApplicationContainer, test_settings: AppSettings
) -> None:
    app: FastAPI = create_app(test_settings, container)

    @app.get("/api/v1/boom")
    async def boom() -> None:
        raise RuntimeError("database password is hunter2")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/boom")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error" and response.json()["request_id"]
    assert "hunter2" not in response.text and "Traceback" not in response.text


async def test_cors_allows_only_configured_origins(api: httpx.AsyncClient) -> None:
    allowed = await api.options(
        "/api/v1/auth/otp/request", headers={"Origin": ORIGIN, "Access-Control-Request-Method": "POST"}
    )
    assert allowed.headers["access-control-allow-origin"] == ORIGIN
    assert allowed.headers["access-control-allow-credentials"] == "true"
    denied = await api.options(
        "/api/v1/auth/otp/request", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"}
    )
    assert "access-control-allow-origin" not in denied.headers


async def test_openapi_is_versioned_and_documents_the_error_free_routes(api: httpx.AsyncClient) -> None:
    schema = (await api.get("/api/openapi.json")).json()
    assert all(path.startswith("/api/v1/") for path in schema["paths"])
    assert {"/api/v1/auth/otp/request", "/api/v1/assistant/ask", "/api/v1/health/ready"} <= set(schema["paths"])


async def test_docs_are_not_exposed_in_production(container: ApplicationContainer) -> None:
    strong = "s" * 40
    settings = AppSettings(
        _env_file=None,
        app_env=AppEnvironment.PRODUCTION,
        otp_hmac_secret=strong,
        session_csrf_secret=strong + "1",
        booking_webhook_secret=strong + "2",
        cors_allowed_origins=["https://davoskarting.ir"],
    )
    transport = httpx.ASGITransport(app=create_app(settings, container), client=(CLIENT_IP, 1))
    async with httpx.AsyncClient(transport=transport, base_url="https://testserver") as client:
        assert (await client.get("/api/openapi.json")).status_code == 404
        assert (await client.get("/api/docs")).status_code == 404
        live = await client.get("/api/v1/health/live")
    assert "strict-transport-security" in live.headers


async def test_production_app_refuses_to_start_with_placeholder_secrets(container: ApplicationContainer) -> None:
    from davos.platform.settings.insecure_configuration_error import InsecureConfigurationError

    with pytest.raises(InsecureConfigurationError):
        create_app(AppSettings(_env_file=None, app_env=AppEnvironment.PRODUCTION), container)
