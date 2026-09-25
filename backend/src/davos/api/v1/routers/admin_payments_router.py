from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.admin_payment_page_response import AdminPaymentPageResponse
from davos.api.schemas.admin_payment_response import AdminPaymentResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.payments.application.ports.payment_query import PaymentQuery
from davos.modules.payments.domain.enums.payment_status import PaymentStatus
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN

router = APIRouter(prefix="/admin/payments", tags=["admin"])


@router.get("", summary="Payment attempts, newest first")
async def search(
    status: PaymentStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    q: str = Query(default="", max_length=100),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    _: AuthenticatedAdminRequest = Depends(require_admin),
    container: ApplicationContainer = Depends(get_container),
) -> AdminPaymentPageResponse:
    page = await container.list_payments().execute(
        PaymentQuery(
            status=status,
            created_from=datetime.combine(date_from, datetime.min.time(), tzinfo=TEHRAN) if date_from else None,
            created_to=(
                datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=TEHRAN) if date_to else None
            ),
            text=q,
            offset=offset,
            limit=limit,
        )
    )
    return AdminPaymentPageResponse(
        items=[AdminPaymentResponse.of(p) for p in page.items],
        total=page.total,
        paid_total_toman=page.paid_total_irr // 10,
    )
