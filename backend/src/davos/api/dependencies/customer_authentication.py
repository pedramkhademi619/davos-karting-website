from __future__ import annotations

from fastapi import Depends, HTTPException, Request

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.container_provider import get_container
from davos.composition.application_container import ApplicationContainer

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


async def require_customer(
    request: Request, container: ApplicationContainer = Depends(get_container)
) -> AuthenticatedRequest:
    """Authenticate the session cookie; for state-changing methods also verify CSRF.

    CSRF defence is layered: SameSite=Lax cookie, an Origin allow-list check, and a per-session
    token echoed in the X-CSRF-Token header.
    """
    raw_token = request.cookies.get(container.settings.session_cookie_name, "")
    customer = await container.authenticate_session().execute(raw_token)
    if customer is None:
        raise HTTPException(status_code=401)

    csrf_token = container.csrf.token_for(raw_token)
    if request.method not in _SAFE_METHODS:
        origin = request.headers.get("origin")
        if origin is not None and origin not in container.settings.cors_allowed_origins:
            raise HTTPException(status_code=403)
        if not container.csrf.is_valid(raw_token, request.headers.get("x-csrf-token", "")):
            raise HTTPException(status_code=403)
    return AuthenticatedRequest(user_id=customer.user_id, session_id=customer.session_id, csrf_token=csrf_token)
