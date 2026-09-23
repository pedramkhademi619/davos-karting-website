from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.booking_return_response import BookingReturnResponse
from davos.api.schemas.webhook_accepted_response import WebhookAcceptedResponse
from davos.composition.application_container import ApplicationContainer
from davos.shared_kernel.domain.errors.payload_too_large_error import PayloadTooLargeError

router = APIRouter(tags=["booking"])

_MAX_WEBHOOK_BYTES = 64 * 1024
_MESSAGES = {
    "pending_confirmation": "در انتظار تایید",
    "pending": "رزرو ثبت شده و در انتظار تایید نهایی است",
    "confirmed": "رزرو شما تایید شد",
    "cancelled": "رزرو لغو شده است",
    "attended": "حضور شما ثبت شده است",
    "no_show": "عدم حضور ثبت شده است",
    "refunded": "وجه رزرو بازگردانده شده است",
}


@router.post(
    "/integrations/booking/webhook",
    status_code=202,
    summary="Signed webhook from the booking system (server-to-server, not for browsers)",
)
async def booking_webhook(
    request: Request, container: ApplicationContainer = Depends(get_container)
) -> WebhookAcceptedResponse:
    if int(request.headers.get("content-length") or 0) > _MAX_WEBHOOK_BYTES:
        raise PayloadTooLargeError
    body = await request.body()
    if len(body) > _MAX_WEBHOOK_BYTES:
        raise PayloadTooLargeError
    outcome = await container.process_booking_webhook().execute(
        raw_body=body, signature_header=request.headers.get("x-davos-signature", "")
    )
    return WebhookAcceptedResponse(outcome=outcome.value)


@router.get("/bookings/return", summary="Result shown after returning from the booking system")
async def booking_return(
    booking: str = Query(min_length=1, max_length=100),
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> BookingReturnResponse:
    """Only the booking reference is read from the URL; the outcome comes from verified server-side data."""
    status = await container.booking_return_status().execute(external_booking_id=booking, user_id=auth.user_id)
    return BookingReturnResponse(
        state=status.state,
        message=_MESSAGES.get(status.state, _MESSAGES["pending_confirmation"]),
        session_time=status.session_time,
        amount_irr=status.amount_irr,
    )
