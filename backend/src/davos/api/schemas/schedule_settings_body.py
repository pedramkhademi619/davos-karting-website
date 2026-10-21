from __future__ import annotations

from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.modules.reservations.domain.enums.junior_scope import JuniorScope
from davos.modules.reservations.domain.value_objects.price_tier import PriceTier
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.shared_kernel.domain.money import Money

_CLOCK = r"^([01][0-9]|2[0-3]):[0-5][0-9]$"


class ScheduleSettingsBody(BaseModel):
    """The owner's booking settings as edited in the admin panel. Prices are in Toman.

    The shift and under-15 fields were added later; a client that does not send them gets the defaults (morning shift
    10:00-14:00, the owner's Saturday-to-Wednesday 15:00-18:00 rule for young drivers).
    """

    online_booking_enabled: bool
    shift_start: str = Field(pattern=_CLOCK)
    shift_end: str = Field(pattern=_CLOCK)
    morning_shift_enabled: bool = True
    morning_start: str = Field(default="10:00", pattern=_CLOCK)
    morning_end: str = Field(default="14:00", pattern=_CLOCK)
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
    open_dates: list[date] = Field(default_factory=list, max_length=400)
    min_days_ahead: int
    max_days_ahead: int
    same_day_lead_minutes: int
    hold_minutes: int
    max_karts_per_reservation: int
    max_active_holds_per_customer: int
    daily_booking_limit_mode: Literal["none", "people", "tickets", "both"]
    daily_people_limit: int | None = Field(default=None, ge=1, le=100_000)
    daily_ticket_limit: int | None = Field(default=None, ge=1, le=100_000)
    junior_weekdays: list[int] = Field(default_factory=lambda: [0, 1, 2, 5, 6])
    junior_from: str = Field(default="15:00", pattern=_CLOCK)
    junior_until: str = Field(default="18:00", pattern=_CLOCK)
    junior_scope: Literal["drivers", "everyone"] = "drivers"

    @model_validator(mode="after")
    def _limit_needs_a_number(self) -> ScheduleSettingsBody:
        mode = self.daily_booking_limit_mode
        if mode in ("people", "both") and self.daily_people_limit is None:
            raise ValueError("سقف تعداد نفرات در روز را وارد کنید.")
        if mode in ("tickets", "both") and self.daily_ticket_limit is None:
            raise ValueError("سقف تعداد تیکت در روز را وارد کنید.")
        return self

    @classmethod
    def of(cls, s: ScheduleSettings) -> ScheduleSettingsBody:
        return cls(
            online_booking_enabled=s.online_booking_enabled,
            shift_start=s.shift_start.strftime("%H:%M"),
            shift_end=s.shift_end.strftime("%H:%M"),
            morning_shift_enabled=s.morning_shift_enabled,
            morning_start=s.morning_start.strftime("%H:%M"),
            morning_end=s.morning_end.strftime("%H:%M"),
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
            open_dates=sorted(s.open_dates),
            min_days_ahead=s.min_days_ahead,
            max_days_ahead=s.max_days_ahead,
            same_day_lead_minutes=s.same_day_lead_minutes,
            hold_minutes=s.hold_minutes,
            max_karts_per_reservation=s.max_karts_per_reservation,
            max_active_holds_per_customer=s.max_active_holds_per_customer,
            daily_booking_limit_mode=s.daily_booking_limit_mode.value,
            daily_people_limit=s.daily_people_limit,
            daily_ticket_limit=s.daily_ticket_limit,
            junior_weekdays=sorted(s.junior_weekdays),
            junior_from=s.junior_from.strftime("%H:%M"),
            junior_until=s.junior_until.strftime("%H:%M"),
            junior_scope=s.junior_scope.value,
        )

    def to_domain(self) -> ScheduleSettings:
        return ScheduleSettings(
            online_booking_enabled=self.online_booking_enabled,
            shift_start=time.fromisoformat(self.shift_start),
            shift_end=time.fromisoformat(self.shift_end),
            morning_shift_enabled=self.morning_shift_enabled,
            morning_start=time.fromisoformat(self.morning_start),
            morning_end=time.fromisoformat(self.morning_end),
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
            open_dates=frozenset(self.open_dates),
            min_days_ahead=self.min_days_ahead,
            max_days_ahead=self.max_days_ahead,
            same_day_lead_minutes=self.same_day_lead_minutes,
            hold_minutes=self.hold_minutes,
            max_karts_per_reservation=self.max_karts_per_reservation,
            max_active_holds_per_customer=self.max_active_holds_per_customer,
            daily_booking_limit_mode=DailyBookingLimitMode(self.daily_booking_limit_mode),
            daily_people_limit=self.daily_people_limit,
            daily_ticket_limit=self.daily_ticket_limit,
            junior_weekdays=frozenset(self.junior_weekdays),
            junior_from=time.fromisoformat(self.junior_from),
            junior_until=time.fromisoformat(self.junior_until),
            junior_scope=JuniorScope(self.junior_scope),
        )
