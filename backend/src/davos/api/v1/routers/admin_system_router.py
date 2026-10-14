from __future__ import annotations

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_permission
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.system_status_response import SystemStatusResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.administration.domain.enums.admin_permission import AdminPermission

router = APIRouter(prefix="/admin/system", tags=["admin"])

_ALLOWED = require_permission(AdminPermission.SYSTEM)


@router.get("/status", summary="Health of the database, Redis, background jobs, SMS, payment gateway and the rest")
async def status(
    _: AuthenticatedAdminRequest = Depends(_ALLOWED), container: ApplicationContainer = Depends(get_container)
) -> SystemStatusResponse:
    return SystemStatusResponse.of(await container.system_status().report())
