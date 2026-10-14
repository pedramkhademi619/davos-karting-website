from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.modules.reservations.domain.value_objects.price_tier import PriceTier
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

# Python weekday numbers (Monday = 0): Thursday = 3, Friday = 4.
THURSDAY_AND_FRIDAY = frozenset({3, 4})
# The owner's current prices (Toman per kart per session).
DEFAULT_NORMAL_PRICES = PriceTier(Money.from_toman(790_000), Money.from_toman(1_000_000))
DEFAULT_HOLIDAY_PRICES = PriceTier(Money.from_toman(940_000), Money.from_toman(1_200_000))


@dataclass(frozen=True)
class ScheduleSettings:
    """Everything the owner can change about online booking, edited in the admin panel.

    Defaults follow the counter's own booking app and the owner's rules: sessions every 10 minutes from 15:00 to
    01:00, six single-seaters and one two-seater per session, booking only for the next day, no booking for Thursday
    and Friday, holiday prices on Thursday and Friday. The session starting at :50 past every hour (16:50, 21:50...)
    is never sold, online or at the counter: the karts are refuelled then.
    """

    online_booking_enabled: bool = True
    shift_start: time = time(15, 0)
    shift_end: time = time(1, 0)  # at or before the start means "after midnight"
    interval_minutes: int = 10
    single_capacity: int = 6
    double_capacity: int = 1
    normal_prices: PriceTier = DEFAULT_NORMAL_PRICES
    holiday_prices: PriceTier = DEFAULT_HOLIDAY_PRICES
    holiday_weekdays: frozenset[int] = THURSDAY_AND_FRIDAY
    closed_weekdays: frozenset[int] = THURSDAY_AND_FRIDAY
    holiday_dates: frozenset[date] = field(default_factory=frozenset)
    closed_dates: frozenset[date] = field(default_factory=frozenset)
    # Single dates opened for online booking although their weekday is closed (e.g. one particular Thursday).
    open_dates: frozenset[date] = field(default_factory=frozenset)
    min_days_ahead: int = 1  # 0 allows booking for the current business day
    max_days_ahead: int = 1
    same_day_lead_minutes: int = 30  # only used when min_days_ahead is 0
    hold_minutes: int = 20
    max_karts_per_reservation: int = 7
    max_active_holds_per_customer: int = 2
    # Off by default: leaves room for walk-in customers by capping today's ONLINE bookings only (never staff
    # entries at the counter), either by total people or by number of tickets regardless of party size.
    daily_booking_limit_mode: DailyBookingLimitMode = DailyBookingLimitMode.NONE
    daily_people_limit: int | None = None  # used by the PEOPLE and BOTH modes
    daily_ticket_limit: int | None = None  # used by the TICKETS and BOTH modes
    # Minutes of the hour at which no session is ever sold -- a fixed safety/operations rule, not a demand cap, so
    # it is never admin-editable and applies to staff counter entries exactly like online bookings.
    blocked_minutes: frozenset[int] = frozenset({50})
    # Online booking (any future date) is refused once the time of day passes this, so customers switch to the
    # counter once the track is actually open; None means online booking never closes for the time of day.
    online_booking_cutoff: time | None = time(15, 0)

    def __post_init__(self) -> None:
        problems: list[str] = []
        if not 5 <= self.interval_minutes <= 120:
            problems.append("فاصله سانس‌ها باید بین ۵ تا ۱۲۰ دقیقه باشد")
        if not (0 <= self.single_capacity <= 50 and 0 <= self.double_capacity <= 50):
            problems.append("ظرفیت خودروها باید بین ۰ تا ۵۰ باشد")
        if self.single_capacity + self.double_capacity == 0:
            problems.append("حداقل یک خودرو باید در هر سانس باشد")
        if not 0 <= self.min_days_ahead <= self.max_days_ahead <= 60:
            problems.append("بازه روزهای قابل رزرو معتبر نیست")
        if not 5 <= self.hold_minutes <= 60:
            problems.append("مدت نگه‌داشتن جا باید بین ۵ تا ۶۰ دقیقه باشد")
        if not 0 <= self.same_day_lead_minutes <= 240:
            problems.append("فاصله رزرو برای همان روز معتبر نیست")
        if not 1 <= self.max_karts_per_reservation <= 50:
            problems.append("سقف خودرو در هر رزرو معتبر نیست")
        if not 1 <= self.max_active_holds_per_customer <= 10:
            problems.append("سقف رزروهای در انتظار پرداخت معتبر نیست")
        if any(not 0 <= d <= 6 for d in self.holiday_weekdays | self.closed_weekdays):
            problems.append("روز هفته معتبر نیست")
        if self.open_dates & self.closed_dates:
            problems.append("یک تاریخ نمی‌تواند هم باز و هم بسته باشد")
        if self.shift_start == self.shift_end:
            problems.append("ساعت شروع و پایان شیفت نباید یکی باشد")
        mode = self.daily_booking_limit_mode
        needs_people = mode in (DailyBookingLimitMode.PEOPLE, DailyBookingLimitMode.BOTH)
        needs_tickets = mode in (DailyBookingLimitMode.TICKETS, DailyBookingLimitMode.BOTH)
        for needed, value in ((needs_people, self.daily_people_limit), (needs_tickets, self.daily_ticket_limit)):
            if needed and not (value is not None and 1 <= value <= 100_000):
                problems.append("سقف رزرو روزانه باید بین ۱ تا ۱۰۰٬۰۰۰ باشد")
                break
        if any(not 0 <= m <= 59 for m in self.blocked_minutes):
            problems.append("دقیقه‌های بدون سانس باید بین ۰ تا ۵۹ باشند")
        if problems:
            raise ValidationError("؛ ".join(problems), code="invalid_schedule_settings")

    def is_holiday(self, day: date) -> bool:
        return day in self.holiday_dates or day.weekday() in self.holiday_weekdays

    def is_closed(self, day: date) -> bool:
        if day in self.closed_dates:
            return True
        return day.weekday() in self.closed_weekdays and day not in self.open_dates

    def prices_for(self, day: date) -> PriceTier:
        return self.holiday_prices if self.is_holiday(day) else self.normal_prices
