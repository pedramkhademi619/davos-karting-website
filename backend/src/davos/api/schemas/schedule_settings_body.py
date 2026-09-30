from __future__ import annotations

from datetime import date, time

from pydantic import BaseModel, Field

from davos.modules.reservations.domain.value_objects.price_tier import PriceTier
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.shared_kernel.domain.money import Money


class ScheduleSettingsBody(BaseModel):
    """The owner's booking settings as edited in the admin panel. Prices are in Toman."""

    online_booking_enabled: bool
    shift_start: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    shift_end: str = Field(pattern=r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
    interval_minutes: int
    single_capacity: int
    double_capacity: int
    normal_single_toman: int = Field(ge=0, le=1_000_000_000)
    normal_double_toman: int = Field(ge=0, le=1_000_000_000)
    holiday_single_toman: int = Field(ge=0, le=1_000_000_000)
    holiday_double_toman: int = Field(ge=0, le=1_000_000_000)
    holiday_weekdays: list[int]
    closed_weekdays: list[int]
    holiday_dates: list[date] = Field(default_factory=list, max_length=400)
    closed_dates: list[date] = Field(default_factory=list, max_length=400)
    min_days_ahead: int
    max_days_ahead: int
    same_day_lead_minutes: int
    hold_minutes: int
    max_karts_per_reservation: int
    max_active_holds_per_customer: int

    @classmethod
    def of(cls, s: ScheduleSettings) -> ScheduleSettingsBody:
        return cls(
            online_booking_enabled=s.online_booking_enabled,
            shift_start=s.shift_start.strftime("%H:%M"),
            shift_end=s.shift_end.strftime("%H:%M"),
            interval_minutes=s.interval_minutes,
            single_capacity=s.single_capacity,
            double_capacity=s.double_capacity,
            normal_single_toman=s.normal_prices.single.irr // 10,
            normal_double_toman=s.normal_prices.double.irr // 10,
            holiday_single_toman=s.holiday_prices.single.irr // 10,
            holiday_double_toman=s.holiday_prices.double.irr // 10,
            holiday_weekdays=sorted(s.holiday_weekdays),
            closed_weekdays=sorted(s.closed_weekdays),
            holiday_dates=sorted(s.holiday_dates),
            closed_dates=sorted(s.closed_dates),
            min_days_ahead=s.min_days_ahead,
            max_days_ahead=s.max_days_ahead,
            same_day_lead_minutes=s.same_day_lead_minutes,
            hold_minutes=s.hold_minutes,
            max_karts_per_reservation=s.max_karts_per_reservation,
            max_active_holds_per_customer=s.max_active_holds_per_customer,
        )

    def to_domain(self) -> ScheduleSettings:
        return ScheduleSettings(
            online_booking_enabled=self.online_booking_enabled,
            shift_start=time.fromisoformat(self.shift_start),
            shift_end=time.fromisoformat(self.shift_end),
            interval_minutes=self.interval_minutes,
            single_capacity=self.single_capacity,
            double_capacity=self.double_capacity,
            normal_prices=PriceTier(
                Money.from_toman(self.normal_single_toman), Money.from_toman(self.normal_double_toman)
            ),
            holiday_prices=PriceTier(
                Money.from_toman(self.holiday_single_toman), Money.from_toman(self.holiday_double_toman)
            ),
            holiday_weekdays=frozenset(self.holiday_weekdays),
            closed_weekdays=frozenset(self.closed_weekdays),
            holiday_dates=frozenset(self.holiday_dates),
            closed_dates=frozenset(self.closed_dates),
            min_days_ahead=self.min_days_ahead,
            max_days_ahead=self.max_days_ahead,
            same_day_lead_minutes=self.same_day_lead_minutes,
            hold_minutes=self.hold_minutes,
            max_karts_per_reservation=self.max_karts_per_reservation,
            max_active_holds_per_customer=self.max_active_holds_per_customer,
        )
