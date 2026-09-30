from __future__ import annotations

from datetime import date, time
from typing import Any

from davos.modules.reservations.domain.value_objects.price_tier import PriceTier
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.shared_kernel.domain.money import Money


class ScheduleSettingsCodec:
    """ScheduleSettings <-> plain JSON. Unknown or missing keys fall back to the defaults, so old rows keep loading."""

    @staticmethod
    def encode(settings: ScheduleSettings) -> dict[str, Any]:
        return {
            "online_booking_enabled": settings.online_booking_enabled,
            "shift_start": settings.shift_start.strftime("%H:%M"),
            "shift_end": settings.shift_end.strftime("%H:%M"),
            "interval_minutes": settings.interval_minutes,
            "single_capacity": settings.single_capacity,
            "double_capacity": settings.double_capacity,
            "normal_prices": {"single": settings.normal_prices.single.irr, "double": settings.normal_prices.double.irr},
            "holiday_prices": {
                "single": settings.holiday_prices.single.irr,
                "double": settings.holiday_prices.double.irr,
            },
            "holiday_weekdays": sorted(settings.holiday_weekdays),
            "closed_weekdays": sorted(settings.closed_weekdays),
            "holiday_dates": sorted(d.isoformat() for d in settings.holiday_dates),
            "closed_dates": sorted(d.isoformat() for d in settings.closed_dates),
            "min_days_ahead": settings.min_days_ahead,
            "max_days_ahead": settings.max_days_ahead,
            "same_day_lead_minutes": settings.same_day_lead_minutes,
            "hold_minutes": settings.hold_minutes,
            "max_karts_per_reservation": settings.max_karts_per_reservation,
            "max_active_holds_per_customer": settings.max_active_holds_per_customer,
        }

    @staticmethod
    def decode(data: dict[str, Any]) -> ScheduleSettings:
        defaults = ScheduleSettings()
        values: dict[str, Any] = {}
        for key in (
            "online_booking_enabled",
            "interval_minutes",
            "single_capacity",
            "double_capacity",
            "min_days_ahead",
            "max_days_ahead",
            "same_day_lead_minutes",
            "hold_minutes",
            "max_karts_per_reservation",
            "max_active_holds_per_customer",
        ):
            if key in data:
                values[key] = data[key]
        for key in ("shift_start", "shift_end"):
            if key in data:
                values[key] = time.fromisoformat(data[key])
        for key in ("normal_prices", "holiday_prices"):
            if key in data:
                values[key] = PriceTier(Money(int(data[key]["single"])), Money(int(data[key]["double"])))
        for key in ("holiday_weekdays", "closed_weekdays"):
            if key in data:
                values[key] = frozenset(int(d) for d in data[key])
        for key in ("holiday_dates", "closed_dates"):
            if key in data:
                values[key] = frozenset(date.fromisoformat(d) for d in data[key])
        return ScheduleSettings(**{**defaults.__dict__, **values})
