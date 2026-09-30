from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query

from davos.api.dependencies.admin_authentication import require_admin, require_owner
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.customer_page_response import CustomerPageResponse
from davos.api.schemas.customer_response import CustomerResponse
from davos.api.schemas.customer_status_request import CustomerStatusRequest
from davos.composition.application_container import ApplicationContainer
from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError

router = APIRouter(prefix="/admin/customers", tags=["admin"])


@router.get("", summary="Search customers by name or mobile")
async def search(
    q: str = Query(default="", max_length=60),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> CustomerPageResponse:
    page = await container.customer_directory().search(text=q, offset=offset, limit=limit)
    return CustomerPageResponse(items=[CustomerResponse.of(u) for u in page.items], total=page.total)


@router.post("/{user_id}/status", summary="Block or unblock a customer (owner only)")
async def set_status(
    user_id: str,
    body: CustomerStatusRequest,
    _: AuthenticatedAdminRequest = Depends(require_owner),
    container: ApplicationContainer = Depends(get_container),
) -> CustomerResponse:
    try:
        target = uuid.UUID(user_id)
    except ValueError as exc:
        raise NotFoundError("مشتری یافت نشد.") from exc
    user = await container.customer_directory().set_status(target, UserStatus(body.status))
    return CustomerResponse.of(user)
