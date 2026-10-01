from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from davos.api.error_handling.error_handlers import ErrorHandlers
from davos.api.middleware.request_id_middleware import RequestIdMiddleware
from davos.api.middleware.security_headers_middleware import SecurityHeadersMiddleware
from davos.api.v1.routers import (
    account_router,
    admin_auth_router,
    admin_customers_router,
    admin_dashboard_router,
    admin_payments_router,
    admin_reservations_router,
    admin_settings_router,
    admin_sms_router,
    admin_users_router,
    assistant_router,
    auth_router,
    booking_router,
    health_router,
    payments_router,
    reservations_router,
)
from davos.composition.application_container import ApplicationContainer
from davos.platform.observability.logging_configurator import LoggingConfigurator
from davos.platform.persistence.startup_lock import StartupLock
from davos.platform.settings.app_settings import AppSettings

API_PREFIX = "/api/v1"

logger = logging.getLogger(__name__)


async def _run_startup_work(container: ApplicationContainer) -> None:
    """Knowledge sync and the first admin account, done by one API worker process only (they all start together)."""
    try:
        async with StartupLock(container.engine, "davos-api-startup").acquired() as mine:
            if not mine:
                logger.info("another API process is doing the start-up work")
                return
            await _sync_assistant_knowledge(container)
            await _bootstrap_owner(container)
    except Exception:
        logger.exception("start-up work failed; the API starts anyway")


async def _bootstrap_owner(container: ApplicationContainer) -> None:
    """Creates the first admin from ADMIN_BOOTSTRAP_* when there is no admin yet. Never changes an existing account."""
    settings = container.settings
    password = settings.admin_bootstrap_password.get_secret_value()
    if not settings.admin_bootstrap_username or not password:
        return
    try:
        created = await container.manage_admins().ensure_bootstrap_owner(
            username=settings.admin_bootstrap_username, password=password
        )
    except Exception:
        logger.exception("the first admin account could not be created from ADMIN_BOOTSTRAP_*")
        return
    if created:
        logger.warning("first admin account created from ADMIN_BOOTSTRAP_USERNAME; remove the password from .env now")


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
        await _run_startup_work(app.state.container)
        # Every worker process loads the embedding model itself, in the background: the API answers at once and the
        # first cached lookup does not pay the second the model takes to load.
        app.state.warm_up = asyncio.create_task(app.state.container.warm_up_answer_cache())
        try:
            yield
        finally:
            app.state.warm_up.cancel()
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
        allow_methods=["GET", "POST", "PUT", "DELETE"],
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
    app.include_router(reservations_router.router, prefix=API_PREFIX)
    app.include_router(account_router.router, prefix=API_PREFIX)
    for admin_router in (
        admin_auth_router,
        admin_dashboard_router,
        admin_reservations_router,
        admin_settings_router,
        admin_customers_router,
        admin_payments_router,
        admin_sms_router,
        admin_users_router,
    ):
        app.include_router(admin_router.router, prefix=API_PREFIX)
    return app
