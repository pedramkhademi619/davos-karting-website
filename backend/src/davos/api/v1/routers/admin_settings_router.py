from __future__ import annotations

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_admin, require_owner
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.schedule_settings_body import ScheduleSettingsBody
from davos.composition.application_container import ApplicationContainer

router = APIRouter(prefix="/admin/settings", tags=["admin"])


@router.get("/schedule", summary="Online booking settings and prices")
async def get_schedule(
    _: AuthenticatedAdminRequest = Depends(require_admin), container: ApplicationContainer = Depends(get_container)
) -> ScheduleSettingsBody:
    return ScheduleSettingsBody.of(await container.schedule_settings().get())


@router.put("/schedule", summary="Replace the online booking settings and prices (owner only)")
async def put_schedule(
    body: ScheduleSettingsBody,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> ScheduleSettingsBody:
    saved = await container.schedule_settings().replace(body.to_domain())
    return ScheduleSettingsBody.of(saved)
