from __future__ import annotations

import logging
import uuid
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.client_ip import client_ip
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.payment_status_response import PaymentStatusResponse
from davos.api.schemas.start_payment_request import StartPaymentRequest
from davos.api.schemas.start_payment_response import StartPaymentResponse
from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
from davos.composition.application_container import ApplicationContainer
from davos.composition.reservation_payment_events import ReservationPaymentEvents
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.modules.payments.domain.errors.payments_disabled_error import PaymentsDisabledError
from davos.shared_kernel.domain.errors.domain_error import DomainError
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError

router = APIRouter(prefix="/payments", tags=["payments"])
logger = logging.getLogger(__name__)

_MAX_CALLBACK_BYTES = 8 * 1024
_CALLBACKS_PER_IP_PER_MINUTE = 30


def _result_page(container: ApplicationContainer, payment_id: uuid.UUID | None) -> RedirectResponse:
    base = container.settings.booking_site_url  # the customer's session cookie lives on the booking site
    target = f"{base}/payment/result?payment={payment_id}" if payment_id else f"{base}/payment/result?error=1"
    return RedirectResponse(target, status_code=303)


async def _limit(container: ApplicationContainer, ip: str) -> None:
    decision = await container.rate_limiter.hit(
        f"payment-callback:ip:{ip}", limit=_CALLBACKS_PER_IP_PER_MINUTE, window_seconds=60
    )
    if not decision.allowed:
        raise RateLimitedError("درخواست‌ها زیاد است.", retry_after_seconds=decision.retry_after_seconds)


async def _finish(container: ApplicationContainer, command: PaymentCallbackCommand) -> RedirectResponse:
    """Verify with the bank, confirm the reservation at once when paid, and send the browser to the result page."""
    try:
        result = await container.handle_payment_callback().execute(command)
    except PaymentNotFoundError:
        logger.warning("payment callback for an unknown attempt")
        return _result_page(container, None)
    except DomainError:
        logger.warning("payment callback could not be processed")
        return _result_page(container, None)
    if result.status is PaymentStatus.PAID:
        try:  # the outbox event does the same; this only makes the ticket appear at once
            await ReservationPaymentEvents(container).payment_succeeded(result.order_ref, str(result.payment_id))
        except Exception:
            logger.exception("reservation confirmation after payment deferred to the event queue")
    return _result_page(container, result.payment_id)


@router.post("", summary="Start a payment for an order (the amount is calculated on the server)")
async def start_payment(
    body: StartPaymentRequest,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> StartPaymentResponse:
    result = await container.start_payment().execute(StartPaymentCommand(body.order_ref, auth.user_id))
    return StartPaymentResponse(
        payment_id=result.payment_id,
        redirect_url=result.redirect_url,
        method=result.method,
        form_fields=result.form_fields,
    )


@router.post("/mellat/callback", include_in_schema=False)
async def mellat_callback(
    request: Request, ip: str = Depends(client_ip), container: ApplicationContainer = Depends(get_container)
) -> RedirectResponse:
    """Bank Mellat posts the customer back here (cross-site form POST, so no session cookie arrives).

    Only RefId, ResCode, SaleOrderId and SaleReferenceId are read; card data in the form is ignored. The result is
    decided by server-to-server verification.
    """
    if not container.settings.payments_enabled:
        raise PaymentsDisabledError
    await _limit(container, ip)
    body = await request.body()
    if len(body) > _MAX_CALLBACK_BYTES:
        return _result_page(container, None)
    form = {k: v[0] for k, v in parse_qs(body.decode("utf-8", errors="replace"), max_num_fields=20).items() if v}
    ref_id = form.get("RefId", "").strip()
    res_code = form.get("ResCode", "").strip()
    sale_order = form.get("SaleOrderId", "").strip()
    sale_reference = form.get("SaleReferenceId", "").strip()
    if not ref_id or len(ref_id) > 64 or not sale_order.isdigit() or len(sale_order) > 19:
        return _result_page(container, None)
    return await _finish(
        container,
        PaymentCallbackCommand(
            authority=ref_id,
            succeeded=res_code == "0",
            gateway_order_id=int(sale_order),
            provider_reference=sale_reference if res_code == "0" and sale_reference else None,
            provider_code=res_code[:10] or None,
        ),
    )


@router.get("/zarinpal/callback", include_in_schema=False)
async def zarinpal_callback(
    authority: str = Query(alias="Authority", min_length=1, max_length=64),
    status: str = Query(alias="Status", max_length=10),
    ip: str = Depends(client_ip),
    container: ApplicationContainer = Depends(get_container),
) -> RedirectResponse:
    if not container.settings.payments_enabled:
        raise PaymentsDisabledError
    await _limit(container, ip)
    return await _finish(container, PaymentCallbackCommand(authority=authority, succeeded=status.upper() == "OK"))


@router.get("/{payment_id}", summary="Status of one of the signed-in customer's payments")
async def payment_status(
    payment_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> PaymentStatusResponse:
    try:
        target = uuid.UUID(payment_id)
    except ValueError as exc:
        raise PaymentNotFoundError from exc
    payment = await container.get_payment_status().execute(payment_id=target, customer_id=auth.user_id)
    return PaymentStatusResponse(
        payment_id=payment.id,
        status=payment.status.value,
        amount_irr=payment.amount.irr,
        amount_toman=payment.amount.irr // 10,  # display conversion; Rial stays the stored base unit
        reference_id=payment.reference_id if payment.status is PaymentStatus.PAID else None,
        reservation_id=ReservationOrderQuotePort.reservation_id_of(payment.order_ref),
    )
