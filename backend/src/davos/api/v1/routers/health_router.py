from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text

from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.readiness_response import ReadinessResponse
from davos.composition.application_container import ApplicationContainer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Liveness: the process is running (no dependencies checked)")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness: dependencies needed to serve traffic are reachable")
async def ready(response: Response, container: ApplicationContainer = Depends(get_container)) -> ReadinessResponse:
    checks = {"database": False, "redis": container.redis is None, "persian_search": False}
    try:
        async with container.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        checks["database"] = True
        checks["persian_search"] = await container.knowledge_search().trigram_support_available()
    except Exception:  # readiness must report, never raise
        logger.warning("readiness: database check failed")
    if container.redis is not None:
        try:
            checks["redis"] = bool(await container.redis.ping())
        except Exception:
            checks["redis"] = False
    healthy = all(checks.values())
    if not healthy:
        response.status_code = 503
    return ReadinessResponse(status="ready" if healthy else "degraded", checks=checks)
