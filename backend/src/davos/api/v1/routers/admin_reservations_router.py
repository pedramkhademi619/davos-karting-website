from __future__ import annotations

import uuid
from datetime import date, time
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.cancel_reservation_request import CancelReservationRequest
from davos.api.schemas.day_availability_response import DayAvailabilityResponse
from davos.api.schemas.reservation_page_response import ReservationPageResponse
from davos.api.schemas.reservation_response import ReservationResponse
from davos.api.schemas.staff_reservation_request import StaffReservationRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.application.use_cases.staff_reservation_command import StaffReservationCommand
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError
from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer

router = APIRouter(prefix="/admin/reservations", tags=["admin"])


def _id(raw: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise ReservationNotFoundError from exc


@router.get("", summary="Search reservations")
async def search(
    date_from: date | None = None,
    date_to: date | None = None,
    status: ReservationStatus | None = None,
    source: ReservationSource | None = None,
    q: str = Query(default="", max_length=60),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationPageResponse:
    page = await container.search_reservations().execute(
        ReservationQuery(
            date_from=date_from,
            date_to=date_to,
            status=status,
            source=source,
            text=DigitNormalizer.to_ascii(q),
            offset=offset,
            limit=limit,
        )
    )
    return ReservationPageResponse(
        items=[ReservationResponse.of(r, staff_view=True) for r in page.items], total=page.total
    )


@router.get("/board", summary="All sessions of one day with free karts (staff view)")
async def board(
    day: Annotated[date, Query(alias="date")],
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> DayAvailabilityResponse:
    return DayAvailabilityResponse.of(await container.day_availability().execute(day, for_staff=True))


@router.post("", status_code=201, summary="Enter karts sold at the counter so they are not sold online")
async def create(
    body: StaffReservationRequest,
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationResponse:
    reservation = await container.create_staff_reservation().execute(
        StaffReservationCommand(
            day=body.date,
            session_time=time.fromisoformat(body.time),
            single_count=body.single_count,
            double_count=body.double_count,
            contact_name=body.contact_name,
            contact_mobile=DigitNormalizer.to_ascii(body.contact_mobile).strip()[:16],
            note=body.note,
            amount_irr=body.amount_toman * 10,
            allow_overbooking=body.allow_overbooking,
        )
    )
    return ReservationResponse.of(reservation, staff_view=True)


@router.post("/{reservation_id}/cancel", summary="Cancel a reservation (a paid one must then be refunded)")
async def cancel(
    reservation_id: str,
    body: CancelReservationRequest,
    auth: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationResponse:
    reason = body.reason.strip() or "لغو توسط مجموعه"
    reservation = await container.staff_update_reservation().cancel(
        _id(reservation_id), f"{reason} ({auth.admin.username})"
    )
    return ReservationResponse.of(reservation, staff_view=True)


@router.post("/{reservation_id}/attended", summary="Check the customer in")
async def attended(
    reservation_id: str,
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationResponse:
    reservation = await container.staff_update_reservation().mark_attended(_id(reservation_id))
    return ReservationResponse.of(reservation, staff_view=True)
