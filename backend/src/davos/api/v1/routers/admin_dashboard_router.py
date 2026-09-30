from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends

from davos.api.dependencies.admin_authentication import require_admin
from davos.api.dependencies.authenticated_admin_request import AuthenticatedAdminRequest
from davos.api.dependencies.container_provider import get_container
from davos.api.schemas.dashboard_response import DashboardResponse
from davos.composition.application_container import ApplicationContainer
from davos.modules.reservations.domain.value_objects.tehran_time import business_date

router = APIRouter(prefix="/admin/dashboard", tags=["admin"])


@router.get("", summary="Today at a glance")
async def dashboard(
    _: AuthenticatedAdminRequest = Depends(require_admin), container: ApplicationContainer = Depends(get_container)
) -> DashboardResponse:
    today = business_date(container.clock.now())
    tomorrow = today + timedelta(days=1)
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    today_stats = await container.reservation_stats().execute(today, today)
    tomorrow_stats = await container.reservation_stats().execute(tomorrow, tomorrow)
    month_stats = await container.reservation_stats().execute(month_start, month_end)
    settings = await container.schedule_settings().get()
    account = await container.sms_panel().account()
    return DashboardResponse(
        today_confirmed=today_stats.confirmed + today_stats.attended,
        today_attended=today_stats.attended,
        today_karts=today_stats.karts,
        today_people=today_stats.people,
        tomorrow_confirmed=tomorrow_stats.confirmed,
        tomorrow_karts=tomorrow_stats.karts,
        month_online_revenue_toman=month_stats.online_revenue_irr // 10,
        month_reservations=month_stats.confirmed + month_stats.attended,
        held_now=today_stats.held + tomorrow_stats.held,
        sms_credit_toman=account.remaining_credit_irr // 10 if account else None,
        payments_enabled=container.settings.payments_enabled,
        online_booking_enabled=settings.online_booking_enabled,
    )
