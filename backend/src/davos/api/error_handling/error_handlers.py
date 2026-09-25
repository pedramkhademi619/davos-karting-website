from __future__ import annotations

import logging
from typing import cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from davos.api.schemas.error_detail import ErrorDetail
from davos.api.schemas.error_response import ErrorResponse
from davos.modules.administration.domain.errors.admin_login_failed_error import AdminLoginFailedError
from davos.modules.booking.domain.errors.invalid_webhook_signature_error import InvalidWebhookSignatureError
from davos.modules.identity.domain.errors.otp_delivery_failed_error import OtpDeliveryFailedError
from davos.modules.identity.domain.errors.otp_verification_failed_error import OtpVerificationFailedError
from davos.shared_kernel.domain.errors.conflict_error import ConflictError
from davos.shared_kernel.domain.errors.domain_error import DomainError
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError
from davos.shared_kernel.domain.errors.payload_too_large_error import PayloadTooLargeError
from davos.shared_kernel.domain.errors.permission_denied_error import PermissionDeniedError
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError
from davos.shared_kernel.domain.errors.validation_error import ValidationError

logger = logging.getLogger(__name__)

# Most specific first: the first matching entry wins.
_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (OtpVerificationFailedError, 401),
    (InvalidWebhookSignatureError, 401),
    (AdminLoginFailedError, 401),
    (PayloadTooLargeError, 413),
    (OtpDeliveryFailedError, 503),
    (RateLimitedError, 429),
    (ValidationError, 422),
    (NotFoundError, 404),
    (ConflictError, 409),
    (PermissionDeniedError, 403),
)
_HTTP_CODES = {401: "unauthenticated", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}
_HTTP_MESSAGES = {401: "برای ادامه وارد شوید.", 403: "دسترسی مجاز نیست.", 404: "مورد درخواستی یافت نشد."}
_GENERIC_400 = "درخواست معتبر نیست."
_GENERIC_500 = "خطای غیرمنتظره‌ای رخ داد. لطفا دوباره تلاش کنید."


def _request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "-"))


def _respond(
    request: Request,
    status: int,
    code: str,
    message: str,
    *,
    details: list[ErrorDetail] | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    body = ErrorResponse(code=code, message=message, details=details or [], request_id=_request_id(request))
    return JSONResponse(status_code=status, content=body.model_dump(), headers=headers)


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    error = cast(DomainError, exc)
    status = next((s for cls, s in _STATUS_BY_ERROR if isinstance(error, cls)), 400)
    headers = None
    if isinstance(error, RateLimitedError):
        headers = {"Retry-After": str(error.retry_after_seconds)}
    return _respond(request, status, error.code, error.message, headers=headers)


async def _validation_error(request: Request, exc: Exception) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    details = [
        ErrorDetail(field=".".join(str(p) for p in item["loc"] if p != "body"), message=str(item["msg"]))
        for item in error.errors()
    ]
    return _respond(request, 422, "validation_error", "داده‌های ارسالی معتبر نیست.", details=details)


async def _http_error(request: Request, exc: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exc)
    return _respond(
        request,
        error.status_code,
        _HTTP_CODES.get(error.status_code, "http_error"),
        _HTTP_MESSAGES.get(error.status_code, _GENERIC_400),
        headers=dict(error.headers or {}),
    )


async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error request_id=%s", _request_id(request), exc_info=exc)
    return _respond(request, 500, "internal_error", _GENERIC_500)


class ErrorHandlers:
    """Turns every failure into the uniform ``{code, message, details, request_id}`` body."""

    @staticmethod
    def install(app: FastAPI) -> None:
        app.add_exception_handler(DomainError, _domain_error)
        app.add_exception_handler(RequestValidationError, _validation_error)
        app.add_exception_handler(StarletteHTTPException, _http_error)
        app.add_exception_handler(Exception, _unhandled)
