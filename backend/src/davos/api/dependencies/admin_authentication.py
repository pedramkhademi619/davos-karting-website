from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, HTTPException, Request

from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.composition.application_container import ApplicationContainer
from davos.modules.administration.domain.enums.admin_permission import AdminPermission
from davos.shared_kernel.domain.errors.permission_denied_error import PermissionDeniedError

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def require_admin(
    request: Request, container: ApplicationContainer = Depends(get_container)
) -> AuthenticatedAdminRequest:
    """Staff session from the admin cookie. State-changing calls also need the same-origin CSRF token."""
    raw_token = request.cookies.get(container.settings.admin_cookie_name, "")
    admin = await container.authenticate_admin().execute(raw_token)
    if admin is None:
        raise HTTPException(status_code=401)
    csrf_token = container.csrf.token_for("admin:" + raw_token)
    if request.method not in _SAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and origin not in container.settings.trusted_origins:
            raise HTTPException(status_code=403)
        if not container.csrf.is_valid("admin:" + raw_token, request.headers.get("x-csrf-token", "")):
            raise HTTPException(status_code=403)
    return AuthenticatedAdminRequest(admin=admin, csrf_token=csrf_token)


async def require_owner(auth: AuthenticatedAdminRequest = Depends(require_admin)) -> AuthenticatedAdminRequest:
    if not auth.admin.is_owner:
        raise HTTPException(status_code=403)
    return auth


def require_permission(permission: AdminPermission) -> Callable[..., Awaitable[AuthenticatedAdminRequest]]:
    """A signed-in staff member who has been given ``permission`` (the owner has all of them).

    Every route of a panel section depends on this, so the menu hiding a section is only a convenience: the server
    refuses the request whatever the browser shows.
    """

    async def check(auth: AuthenticatedAdminRequest = Depends(require_admin)) -> AuthenticatedAdminRequest:
        if not auth.admin.can(permission):
            raise PermissionDeniedError("شما اجازه دسترسی به این بخش را ندارید.")
        return auth

    return check
