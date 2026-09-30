from __future__ import annotations

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    today_confirmed: int
    today_attended: int
    today_karts: int
    today_people: int
    tomorrow_confirmed: int
    tomorrow_karts: int
    month_online_revenue_toman: int
    month_reservations: int
    held_now: int
    sms_credit_toman: int | None
    payments_enabled: bool
    online_booking_enabled: bool
