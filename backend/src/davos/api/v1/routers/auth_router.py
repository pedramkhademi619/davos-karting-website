from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Request, Response

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.client_ip import client_ip
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.me_response import MeResponse
from davos.api.schemas.request_otp_request import RequestOtpRequest
from davos.api.schemas.request_otp_response import RequestOtpResponse
from davos.api.schemas.session_response import SessionResponse
from davos.api.schemas.signed_in_response import SignedInResponse
from davos.api.schemas.verify_otp_request import VerifyOtpRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.identity.application.use_cases.request_otp_command import RequestOtpCommand
from davos.modules.identity.application.use_cases.verify_otp_command import VerifyOtpCommand
from davos.modules.identity.domain.errors.session_not_found_error import SessionNotFoundError

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", summary="Send a one-time code by SMS", response_model_exclude_none=True)
async def request_otp(
    body: RequestOtpRequest,
    ip: str = Depends(client_ip),
    container: ApplicationContainer = Depends(get_container),
) -> RequestOtpResponse:
    result = await container.request_otp().execute(RequestOtpCommand(raw_mobile=body.mobile, client_ip=ip))
    return RequestOtpResponse(
        expires_in_seconds=result.expires_in_seconds,
        resend_after_seconds=result.resend_after_seconds,
        dev_code=container.dev_otp_code(body.mobile),
    )


@router.post("/otp/verify", summary="Exchange a one-time code for a session cookie")
async def verify_otp(
    body: VerifyOtpRequest,
    request: Request,
    response: Response,
    ip: str = Depends(client_ip),
    container: ApplicationContainer = Depends(get_container),
) -> SignedInResponse:
    result = await container.verify_otp().execute(
        VerifyOtpCommand(
            raw_mobile=body.mobile,
            code=body.code,
            client_ip=ip,
            user_agent=request.headers.get("user-agent", ""),
        )
    )
    settings = container.settings
    response.set_cookie(
        settings.session_cookie_name,
        result.session_token,
        max_age=settings.session_lifetime_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    return SignedInResponse(
        user_id=result.user_id,
        is_new_user=result.is_new_user,
        expires_at=result.expires_at,
        csrf_token=container.csrf.token_for(result.session_token),
    )


@router.get("/me", summary="Current customer and CSRF token")
async def me(auth: AuthenticatedRequest = Depends(require_customer)) -> MeResponse:
    return MeResponse(user_id=auth.user_id, csrf_token=auth.csrf_token)


@router.get("/sessions", summary="Devices signed in to this account")
async def list_sessions(
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> list[SessionResponse]:
    sessions = await container.list_sessions().execute(user_id=auth.user_id, current_session_id=auth.session_id)
    return [
        SessionResponse(
            session_id=s.session_id,
            user_agent=s.user_agent,
            ip_hint=s.ip_hint,
            created_at=s.created_at,
            last_seen_at=s.last_seen_at,
            is_current=s.is_current,
        )
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=204, summary="Sign a device out")
async def revoke_session(
    session_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    try:
        target = uuid.UUID(session_id)
    except ValueError as exc:
        raise SessionNotFoundError from exc
    await container.revoke_session().execute(user_id=auth.user_id, session_id=target)
    return Response(status_code=204)


@router.post("/logout", status_code=204, summary="Sign out of the current device")
async def logout(
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.revoke_session().execute(user_id=auth.user_id, session_id=auth.session_id)
    out = Response(status_code=204)
    out.delete_cookie(container.settings.session_cookie_name, path="/")
    return out
