from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_owner
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.admin_active_request import AdminActiveRequest
from davos.api.schemas.admin_user_response import AdminUserResponse
from davos.api.schemas.create_admin_request import CreateAdminRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get("", summary="Staff accounts (owner only)")
async def list_admins(
    _: AuthenticatedAdminRequest = Depends(require_owner), container: ApplicationContainer = Depends(get_container)
) -> list[AdminUserResponse]:
    return [AdminUserResponse.of(a) for a in await container.manage_admins().list_all()]


@router.post("", status_code=201, summary="Add a staff account (owner only)")
async def create_admin(
    body: CreateAdminRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> AdminUserResponse:
    admin = await container.manage_admins().create(
        username=body.username, display_name=body.display_name, password=body.password, role=AdminRole(body.role)
    )
    return AdminUserResponse.of(admin)


@router.post("/{admin_id}/active", summary="Enable or disable a staff account (owner only)")
async def set_active(
    admin_id: str,
    body: AdminActiveRequest,
    auth: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> AdminUserResponse:
    try:
        target = uuid.UUID(admin_id)
    except ValueError as exc:
        raise NotFoundError("کاربر یافت نشد.") from exc
    admin = await container.manage_admins().set_active(
        admin_id=target, active=body.is_active, acting_admin_id=auth.admin.admin_id
    )
    return AdminUserResponse.of(admin)
