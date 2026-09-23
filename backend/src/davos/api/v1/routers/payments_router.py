from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.payment_status_response import PaymentStatusResponse
from davos.api.schemas.start_payment_request import StartPaymentRequest
from davos.api.schemas.start_payment_response import StartPaymentResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.payments.application.use_cases.payment_callback_command import PaymentCallbackCommand
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.payments.domain.errors.payment_not_found_error import PaymentNotFoundError
from davos.modules.payments.domain.errors.payments_disabled_error import PaymentsDisabledError

router = APIRouter(prefix="/payments", tags=["payments"])


def _require_enabled(container: ApplicationContainer) -> None:
    if not container.settings.payments_enabled:
        raise PaymentsDisabledError


@router.post("", summary="Start a payment for an order (the amount is calculated on the server)")
async def start_payment(
    body: StartPaymentRequest,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> StartPaymentResponse:
    result = await container.start_payment().execute(StartPaymentCommand(body.order_ref, auth.user_id))
    return StartPaymentResponse(payment_id=result.payment_id, redirect_url=result.redirect_url)


@router.get("/callback", summary="Browser return from the gateway; triggers server-side verification")
async def payment_callback(
    authority: str = Query(alias="Authority", min_length=1, max_length=64),
    status: str = Query(alias="Status", max_length=10),
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> PaymentStatusResponse:
    """The query string only identifies the attempt. The result is decided by the provider, never by the URL."""
    _require_enabled(container)
    result = await container.handle_payment_callback().execute(
        PaymentCallbackCommand(authority=authority, status_param=status, customer_id=auth.user_id)
    )
    return PaymentStatusResponse(payment_id=result.payment_id, status=result.status.value)


@router.get("/{payment_id}", summary="Status of one of the signed-in customer's payments")
async def payment_status(
    payment_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> PaymentStatusResponse:
    _require_enabled(container)
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
        reference_id=payment.reference_id,
    )
