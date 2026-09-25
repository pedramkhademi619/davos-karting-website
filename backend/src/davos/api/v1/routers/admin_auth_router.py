from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.client_ip import client_ip
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.admin_login_request import AdminLoginRequest
from davos.api.schemas.admin_me_response import AdminMeResponse
from davos.api.schemas.change_password_request import ChangePasswordRequest
from davos.composition.application_container import ApplicationContainer

router = APIRouter(prefix="/admin/auth", tags=["admin"])

COOKIE_PATH = "/api/v1/admin"


@router.post("/login", summary="Staff sign-in")
async def login(
    body: AdminLoginRequest,
    request: Request,
    response: Response,
    ip: str = Depends(client_ip),
    container: ApplicationContainer = Depends(get_container),
) -> AdminMeResponse:
    result = await container.admin_login().execute(
        username=body.username, password=body.password, client_ip=ip, user_agent=request.headers.get("user-agent", "")
    )
    settings = container.settings
    response.set_cookie(
        settings.admin_cookie_name,
        result.token,
        max_age=settings.admin_session_hours * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path=COOKIE_PATH,
    )
    return AdminMeResponse(
        admin_id=result.admin.admin_id,
        username=result.admin.username,
        display_name=result.admin.display_name,
        role=result.admin.role.value,
        csrf_token=container.csrf.token_for("admin:" + result.token),
    )


@router.get("/me", summary="Current staff member and CSRF token")
async def me(auth: AuthenticatedAdminRequest = Depends(require_admin)) -> AdminMeResponse:
    admin = auth.admin
    return AdminMeResponse(
        admin_id=admin.admin_id,
        username=admin.username,
        display_name=admin.display_name,
        role=admin.role.value,
        csrf_token=auth.csrf_token,
    )


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.admin_logout().execute(request.cookies.get(container.settings.admin_cookie_name, ""))
    out = Response(status_code=204)
    out.delete_cookie(container.settings.admin_cookie_name, path=COOKIE_PATH)
    return out


@router.post("/password", status_code=204, summary="Change the signed-in staff member's password")
async def change_password(
    body: ChangePasswordRequest,
    auth: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.manage_admins().change_own_password(
        admin_id=auth.admin.admin_id, current=body.current_password, new=body.new_password
    )
    return Response(status_code=204)
