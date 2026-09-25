from __future__ import annotations

import uuid
from datetime import date, time
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.bookable_day_response import BookableDayResponse
from davos.api.schemas.booking_calendar_response import BookingCalendarResponse
from davos.api.schemas.create_reservation_request import CreateReservationRequest
from davos.api.schemas.day_availability_response import DayAvailabilityResponse
from davos.api.schemas.reservation_response import ReservationResponse
from davos.api.schemas.start_payment_response import StartPaymentResponse
from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
from davos.composition.application_container import ApplicationContainer
from davos.modules.payments.application.use_cases.start_payment_command import StartPaymentCommand
from davos.modules.reservations.application.use_cases.hold_reservation_command import HoldReservationCommand
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError

router = APIRouter(prefix="/reservations", tags=["reservations"])


def _reservation_id(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise ReservationNotFoundError from exc


@router.get("/calendar", summary="Days that can be booked online right now, with prices")
async def calendar(container: ApplicationContainer = Depends(get_container)) -> BookingCalendarResponse:
    result = await container.booking_calendar().execute()
    return BookingCalendarResponse(
        online_booking_enabled=result.online_booking_enabled,
        payments_enabled=container.settings.payments_enabled,
        hold_minutes=result.hold_minutes,
        max_karts_per_reservation=result.max_karts_per_reservation,
        days=[BookableDayResponse.of(d) for d in result.days],
    )


@router.get("/availability", summary="Every session of one day with the karts still free")
async def availability(
    day: Annotated[date, Query(alias="date")], container: ApplicationContainer = Depends(get_container)
) -> DayAvailabilityResponse:
    return DayAvailabilityResponse.of(await container.day_availability().execute(day))


@router.post("", status_code=201, summary="Hold karts in a session while the customer pays")
async def create_reservation(
    body: CreateReservationRequest,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationResponse:
    profile = await container.customer_profile().get(auth.user_id)
    name = body.contact_name.strip() or profile.full_name
    reservation = await container.hold_reservation().execute(
        HoldReservationCommand(
            customer_id=auth.user_id,
            day=body.date,
            session_time=time.fromisoformat(body.time),
            single_count=body.single_count,
            double_count=body.double_count,
            contact_name=name,
            contact_mobile=profile.mobile.local,
        )
    )
    return ReservationResponse.of(reservation)


@router.post("/{reservation_id}/pay", summary="Start paying a held reservation (the amount comes from the server)")
async def pay_reservation(
    reservation_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> StartPaymentResponse:
    target = _reservation_id(reservation_id)
    result = await container.start_payment().execute(
        StartPaymentCommand(order_ref=ReservationOrderQuotePort.order_ref_for(target), customer_id=auth.user_id)
    )
    return StartPaymentResponse(
        payment_id=result.payment_id,
        redirect_url=result.redirect_url,
        method=result.method,
        form_fields=result.form_fields,
    )


@router.delete("/{reservation_id}", status_code=204, summary="Release karts that have not been paid for")
async def cancel_hold(
    reservation_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> Response:
    await container.cancel_own_hold().execute(customer_id=auth.user_id, reservation_id=_reservation_id(reservation_id))
    return Response(status_code=204)
