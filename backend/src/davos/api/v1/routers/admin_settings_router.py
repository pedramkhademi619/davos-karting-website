from __future__ import annotations

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_permission
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.schedule_settings_body import ScheduleSettingsBody
from davos.composition.application_container import ApplicationContainer
from davos.modules.administration.domain.enums.admin_permission import AdminPermission

router = APIRouter(prefix="/admin/settings", tags=["admin"])

_VIEW = require_permission(AdminPermission.SETTINGS)
_MANAGE = require_permission(AdminPermission.SETTINGS_MANAGE)


@router.get("/schedule", summary="Online booking settings and prices")
async def get_schedule(
    _: AuthenticatedAdminRequest = Depends(_VIEW), container: ApplicationContainer = Depends(get_container)
) -> ScheduleSettingsBody:
    return ScheduleSettingsBody.of(await container.schedule_settings().get())


@router.put("/schedule", summary="Replace the online booking settings and prices (owner only)")
async def put_schedule(
    body: ScheduleSettingsBody,
    _: AuthenticatedAdminRequest = Depends(_MANAGE),
    container: ApplicationContainer = Depends(get_container),
) -> ScheduleSettingsBody:
    saved = await container.schedule_settings().replace(body.to_domain())
    return ScheduleSettingsBody.of(saved)
