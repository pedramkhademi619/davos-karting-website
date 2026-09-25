from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from davos.api.dependencies.authenticated_request import AuthenticatedRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.dependencies.customer_authentication import require_customer
from davos.api.schemas.profile_response import ProfileResponse
from davos.api.schemas.reservation_response import ReservationResponse
from davos.api.schemas.update_profile_request import UpdateProfileRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.reservations.domain.errors.reservation_not_found_error import ReservationNotFoundError

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/profile", summary="The signed-in customer's profile")
async def get_profile(
    auth: AuthenticatedRequest = Depends(require_customer), container: ApplicationContainer = Depends(get_container)
) -> ProfileResponse:
    return ProfileResponse.of(await container.customer_profile().get(auth.user_id))


@router.put("/profile", summary="Update name and SMS news consent")
async def update_profile(
    body: UpdateProfileRequest,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> ProfileResponse:
    user = await container.customer_profile().update(
        auth.user_id, full_name=body.full_name, marketing_opt_in=body.marketing_opt_in
    )
    return ProfileResponse.of(user)


@router.get("/reservations", summary="The customer's tickets, newest first")
async def my_reservations(
    auth: AuthenticatedRequest = Depends(require_customer), container: ApplicationContainer = Depends(get_container)
) -> list[ReservationResponse]:
    items = await container.customer_reservations().for_customer(auth.user_id)
    return [ReservationResponse.of(r) for r in items]


@router.get("/reservations/{reservation_id}", summary="One of the customer's tickets")
async def my_reservation(
    reservation_id: str,
    auth: AuthenticatedRequest = Depends(require_customer),
    container: ApplicationContainer = Depends(get_container),
) -> ReservationResponse:
    try:
        target = uuid.UUID(reservation_id)
    except ValueError as exc:
        raise ReservationNotFoundError from exc
    return ReservationResponse.of(await container.customer_reservations().one(auth.user_id, target))
