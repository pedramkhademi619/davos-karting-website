from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.send_sms_request import SendSmsRequest
from davos.api.schemas.send_sms_response import SendSmsResponse
from davos.api.schemas.sms_account_response import SmsAccountResponse
from davos.api.schemas.sms_log_page_response import SmsLogPageResponse
from davos.api.schemas.sms_log_response import SmsLogResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.shared_kernel.domain.errors.validation_error import ValidationError

router = APIRouter(prefix="/admin/sms", tags=["admin"])


@router.get("/account", summary="SMS provider and remaining credit")
async def account(
    _: AuthenticatedAdminRequest = Depends(require_admin), container: ApplicationContainer = Depends(get_container)
) -> SmsAccountResponse:
    info = await container.sms_panel().account()
    provider = container.settings.sms_provider
    if info is None:
        return SmsAccountResponse(provider=provider, connected=False)
    return SmsAccountResponse(
        provider=provider,
        connected=True,
        remaining_credit_toman=info.remaining_credit_irr // 10,
        expires_at=info.expires_at,
    )


@router.get("/messages", summary="Sent messages with delivery status")
async def messages(
    q: str = Query(default="", max_length=60),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> SmsLogPageResponse:
    page = await container.sms_panel().history(text=q, offset=offset, limit=limit)
    return SmsLogPageResponse(items=[SmsLogResponse.of(e) for e in page.items], total=page.total)


@router.post("/send", summary="Send one text to typed numbers, news subscribers or the customers of one day")
async def send(
    body: SendSmsRequest,
    auth: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> SendSmsResponse:
    recipients = await _recipients(body, container)
    report = await container.send_bulk_sms().execute(recipients=recipients, text=body.text, sent_by=auth.admin.username)
    return SendSmsResponse(
        batch_id=report.batch_id, accepted=report.accepted, failed=report.failed, invalid_numbers=report.invalid_numbers
    )


async def _recipients(body: SendSmsRequest, container: ApplicationContainer) -> list[str]:
    if body.audience == "numbers":
        return body.numbers
    if body.audience == "subscribers":
        return [m.local for m in await container.customer_directory().marketing_audience()]
    if body.day is None:
        raise ValidationError("روز را انتخاب کنید.", code="sms_day_missing")
    numbers: list[str] = []
    offset = 0
    while True:
        page = await container.search_reservations().execute(
            ReservationQuery(date_from=body.day, date_to=body.day, offset=offset, limit=200)
        )
        numbers.extend(
            r.contact_mobile
            for r in page.items
            if r.contact_mobile and r.status in {ReservationStatus.CONFIRMED, ReservationStatus.ATTENDED}
        )
        offset += len(page.items)
        if not page.items or offset >= page.total:
            return numbers
