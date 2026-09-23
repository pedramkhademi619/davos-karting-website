from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from davos.api.error_handling.error_handlers import ErrorHandlers
from davos.api.middleware.request_id_middleware import RequestIdMiddleware
from davos.api.middleware.security_headers_middleware import SecurityHeadersMiddleware
from davos.api.v1.routers import assistant_router, auth_router, booking_router, health_router, payments_router
from davos.composition.application_container import ApplicationContainer
from davos.platform.observability.logging_configurator import LoggingConfigurator
from davos.platform.settings.app_settings import AppSettings

API_PREFIX = "/api/v1"

logger = logging.getLogger(__name__)


async def _sync_assistant_knowledge(container: ApplicationContainer) -> None:
    """Publishes the owner's knowledge files at start-up. A problem is logged and never stops the API from starting."""
    use_case = container.sync_knowledge_documents()
    if use_case is None:
        return
    try:
        report = await use_case.execute()
    except Exception:
        logger.exception("assistant knowledge sync failed; the assistant keeps whatever was published before")
        return
    logger.info(
        "assistant knowledge synced: published=%d drafts=%d removed=%d problems=%d",
        report.published,
        report.drafts,
        report.removed,
        len(report.problems),
    )
    for problem in report.problems:
        logger.warning("knowledge file %s.txt is not used: %s", problem.name, problem.reason)


def create_app(settings: AppSettings, container: ApplicationContainer | None = None) -> FastAPI:
    """Build the ASGI application. A pre-built container is injected by tests."""
    settings.validate_for_environment()
    LoggingConfigurator.install(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        owned = container is None
        app.state.container = container or ApplicationContainer.build(settings)
        await _sync_assistant_knowledge(app.state.container)
        try:
            yield
        finally:
            if owned:
                await app.state.container.aclose()

    docs_enabled = not settings.is_production
    app = FastAPI(
        title="Davos Karting API",
        version="1.0.0",
        description="Modular monolith (hexagonal). All business rules live here; the web app only renders.",
        lifespan=lifespan,
        docs_url="/api/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if docs_enabled else None,
    )
    if container is not None:  # tests use httpx without running lifespan events
        app.state.container = container

    ErrorHandlers.install(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Content-Type", "X-CSRF-Token", "X-Request-ID", "Idempotency-Key"],
        max_age=600,
    )
    app.add_middleware(SecurityHeadersMiddleware, hsts=settings.is_production)
    app.add_middleware(RequestIdMiddleware)

    app.include_router(health_router.router, prefix=API_PREFIX)
    app.include_router(auth_router.router, prefix=API_PREFIX)
    app.include_router(assistant_router.router, prefix=API_PREFIX)
    app.include_router(booking_router.router, prefix=API_PREFIX)
    app.include_router(payments_router.router, prefix=API_PREFIX)
    return app
