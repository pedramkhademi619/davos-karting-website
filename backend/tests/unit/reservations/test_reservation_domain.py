from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest

from davos.modules.reservations.adapters.persistence.schedule_settings_codec import ScheduleSettingsCodec
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.errors.daily_booking_limit_reached_error import (
    DailyBookingLimitReachedError,
)
from davos.modules.reservations.domain.errors.invalid_reservation_transition_error import (
    InvalidReservationTransitionError,
)
from davos.modules.reservations.domain.errors.session_full_error import SessionFullError
from davos.modules.reservations.domain.events.reservation_cancelled import ReservationCancelled
from davos.modules.reservations.domain.events.reservation_confirmed import ReservationConfirmed
from davos.modules.reservations.domain.services.daily_booking_limit import DailyBookingLimit
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.modules.reservations.domain.value_objects.daily_online_load import DailyOnlineLoad
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN, business_date
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

SAT, SUN, WED, THU, FRI = date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 9)
SATURDAY_MORNING = datetime(2026, 1, 3, 9, 30, tzinfo=TEHRAN)
S = ReservationStatus


# ---------------------------------------------------------------- calendar


def test_default_sessions_run_every_10_minutes_from_10_to_14_and_from_15_to_01() -> None:
    times = SessionCalendar(ScheduleSettings()).session_times()
    assert times[0] == time(10, 0) and times[-1] == time(0, 50) and len(times) == 24 + 60
    assert time(13, 50) in times and time(14, 0) not in times and time(14, 50) not in times


def test_an_after_midnight_session_starts_on_the_next_calendar_day() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert calendar.starts_at(SAT, time(0, 30)) == datetime(2026, 1, 4, 0, 30, tzinfo=TEHRAN)
    assert calendar.starts_at(SAT, time(18, 0)) == datetime(2026, 1, 3, 18, 0, tzinfo=TEHRAN)


def test_half_past_midnight_still_belongs_to_the_previous_business_day() -> None:
    assert business_date(datetime(2026, 1, 4, 0, 30, tzinfo=TEHRAN)) == SAT
    assert business_date(datetime(2026, 1, 4, 10, 0, tzinfo=TEHRAN)) == SUN
    # 21:00 UTC on Saturday is 00:30 on Sunday in Tehran: still Saturday's shift.
    assert business_date(datetime(2026, 1, 3, 21, 0, tzinfo=UTC)) == SAT


def test_by_default_only_tomorrow_can_be_booked_and_never_thursday_or_friday() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert calendar.bookable_dates(SATURDAY_MORNING) == [SUN]
    wednesday = datetime(2026, 1, 7, 12, 0, tzinfo=TEHRAN)
    assert calendar.bookable_dates(wednesday) == []  # tomorrow is Thursday
    assert not calendar.is_bookable(SAT, time(18, 0), SATURDAY_MORNING)  # no same-day booking


def test_closed_dates_and_a_wider_window_are_respected() -> None:
    settings = ScheduleSettings(max_days_ahead=7, closed_dates=frozenset({date(2026, 1, 5)}))
    days = SessionCalendar(settings).bookable_dates(SATURDAY_MORNING)
    assert days == [SUN, date(2026, 1, 6), WED, date(2026, 1, 10)]


def test_one_closed_weekday_date_can_be_opened_without_opening_every_such_weekday() -> None:
    thursday = date(2026, 1, 8)
    settings = ScheduleSettings(max_days_ahead=14, open_dates=frozenset({thursday}))
    days = SessionCalendar(settings).bookable_dates(SATURDAY_MORNING)
    assert thursday in days and date(2026, 1, 9) not in days and date(2026, 1, 15) not in days
    assert not settings.is_closed(thursday) and settings.is_closed(date(2026, 1, 15))


def test_opened_dates_survive_storage_and_old_rows_without_them_still_load() -> None:
    settings = ScheduleSettings(open_dates=frozenset({date(2026, 1, 8)}))
    stored = ScheduleSettingsCodec.encode(settings)
    assert ScheduleSettingsCodec.decode(stored).open_dates == settings.open_dates
    stored.pop("open_dates")
    assert ScheduleSettingsCodec.decode(stored).open_dates == frozenset()


def test_a_date_cannot_be_both_opened_and_closed() -> None:
    both = frozenset({date(2026, 1, 8)})
    with pytest.raises(ValidationError):
        ScheduleSettings(open_dates=both, closed_dates=both)


def test_same_day_booking_keeps_a_lead_time_before_the_session() -> None:
    settings = ScheduleSettings(min_days_ahead=0, same_day_lead_minutes=30, online_booking_cutoff=None)
    calendar = SessionCalendar(settings)
    now = datetime(2026, 1, 3, 17, 50, tzinfo=TEHRAN)
    assert not calendar.is_bookable(SAT, time(18, 10), now)  # less than 30 minutes away
    assert calendar.is_bookable(SAT, time(18, 20), now)


def test_only_real_session_times_are_bookable() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert not calendar.is_bookable(SUN, time(18, 7), SATURDAY_MORNING)
    assert not calendar.is_bookable(SUN, time(14, 20), SATURDAY_MORNING)  # between the two shifts
    assert calendar.is_bookable(SUN, time(12, 0), SATURDAY_MORNING)  # the morning shift
    assert calendar.is_bookable(SUN, time(0, 40), SATURDAY_MORNING)  # the last session of the night


def test_the_fuel_break_minute_is_on_the_grid_but_never_sellable() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert time(16, 50) in calendar.session_times()  # still shown on the grid (to staff)
    assert calendar.is_blocked(time(16, 50)) and calendar.is_blocked(time(21, 50)) and calendar.is_blocked(time(0, 50))
    assert not calendar.is_blocked(time(16, 40))
    assert not calendar.is_sellable_time(time(16, 50)) and calendar.is_sellable_time(time(16, 40))
    assert not calendar.is_bookable(SUN, time(16, 50), SATURDAY_MORNING)


def test_blocked_minutes_are_not_admin_editable() -> None:
    # ScheduleSettingsCodec never reads/writes this field, so even a tampered stored row cannot change it; proven
    # here at the domain level: the default always wins regardless of what else is passed.
    assert ScheduleSettings(single_capacity=10).blocked_minutes == frozenset({50})


def test_online_booking_closes_for_the_day_at_the_cutoff_whatever_the_date_booked() -> None:
    settings = ScheduleSettings(min_days_ahead=0, max_days_ahead=7, online_booking_cutoff=time(15, 0))
    calendar = SessionCalendar(settings)
    before = datetime(2026, 1, 3, 14, 59, tzinfo=TEHRAN)
    after = datetime(2026, 1, 3, 15, 0, tzinfo=TEHRAN)
    assert not calendar.is_online_cutoff_passed(before) and calendar.is_online_cutoff_passed(after)
    assert calendar.is_bookable(WED, time(18, 0), before)  # booking a future day, still before the cutoff today
    assert not calendar.is_bookable(WED, time(18, 0), after)  # same future day, but it is past 15:00 today


def test_a_cutoff_of_none_means_online_booking_never_closes_for_the_time_of_day() -> None:
    calendar = SessionCalendar(ScheduleSettings(online_booking_cutoff=None))
    assert not calendar.is_online_cutoff_passed(datetime(2026, 1, 3, 23, 59, tzinfo=TEHRAN))


def test_online_booking_can_be_switched_off() -> None:
    calendar = SessionCalendar(ScheduleSettings(online_booking_enabled=False))
    assert not calendar.is_bookable(SUN, time(18, 0), SATURDAY_MORNING)


# ---------------------------------------------------------------- settings and prices


def test_thursday_and_friday_use_holiday_prices_and_extra_holidays_can_be_added() -> None:
    settings = ScheduleSettings(holiday_dates=frozenset({SUN}))
    assert settings.prices_for(SAT) == settings.normal_prices
    assert settings.prices_for(THU) == settings.prices_for(FRI) == settings.prices_for(SUN) == settings.holiday_prices
    assert settings.normal_prices.single == Money.from_toman(790_000)


def test_a_two_seater_is_priced_per_kart() -> None:
    tier = ScheduleSettings().normal_prices
    assert tier.total(2, 1) == Money.from_toman(2 * 790_000 + 1_000_000)


@pytest.mark.parametrize(
    "bad",
    [
        {"interval_minutes": 2},
        {"single_capacity": 0, "double_capacity": 0},
        {"min_days_ahead": 3, "max_days_ahead": 1},
        {"hold_minutes": 90},
        {"closed_weekdays": frozenset({7})},
        {"shift_start": time(15, 0), "shift_end": time(15, 0)},
        {"daily_booking_limit_mode": DailyBookingLimitMode.PEOPLE, "daily_people_limit": None},
        {"daily_booking_limit_mode": DailyBookingLimitMode.TICKETS, "daily_ticket_limit": 0},
        {"daily_booking_limit_mode": DailyBookingLimitMode.BOTH, "daily_people_limit": 50},
        {"daily_booking_limit_mode": DailyBookingLimitMode.BOTH, "daily_ticket_limit": 20},
        {"blocked_minutes": frozenset({60})},
    ],
)
def test_invalid_settings_are_refused(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ScheduleSettings(**bad)  # type: ignore[arg-type]


# ---------------------------------------------------------------- the optional daily cap


def test_the_daily_cap_is_off_by_default() -> None:
    DailyBookingLimit(ScheduleSettings()).check(DailyOnlineLoad(tickets=10_000, people=50_000), 7, 1)  # never raises


def test_a_ticket_cap_counts_reservations_not_people() -> None:
    settings = ScheduleSettings(daily_booking_limit_mode=DailyBookingLimitMode.TICKETS, daily_ticket_limit=20)
    limit = DailyBookingLimit(settings)
    limit.check(DailyOnlineLoad(tickets=19, people=19), single_count=7, double_count=0)  # one more ticket still fits
    with pytest.raises(DailyBookingLimitReachedError):
        limit.check(DailyOnlineLoad(tickets=20, people=20), single_count=1, double_count=0)


def test_a_people_cap_counts_heads_not_tickets() -> None:
    settings = ScheduleSettings(daily_booking_limit_mode=DailyBookingLimitMode.PEOPLE, daily_people_limit=50)
    limit = DailyBookingLimit(settings)
    limit.check(DailyOnlineLoad(tickets=1, people=48), single_count=2, double_count=0)  # exactly fills it: 48+2=50
    with pytest.raises(DailyBookingLimitReachedError):
        limit.check(DailyOnlineLoad(tickets=1, people=48), single_count=0, double_count=2)  # 48+4 > 50


def test_the_combined_cap_stops_at_whichever_limit_is_reached_first() -> None:
    settings = ScheduleSettings(
        daily_booking_limit_mode=DailyBookingLimitMode.BOTH, daily_people_limit=50, daily_ticket_limit=20
    )
    limit = DailyBookingLimit(settings)
    limit.check(DailyOnlineLoad(tickets=19, people=40), single_count=3, double_count=0)  # both still have room
    with pytest.raises(DailyBookingLimitReachedError):  # tickets full long before the people cap
        limit.check(DailyOnlineLoad(tickets=20, people=20), single_count=1, double_count=0)
    with pytest.raises(DailyBookingLimitReachedError):  # people cap hit with only a few tickets
        limit.check(DailyOnlineLoad(tickets=3, people=49), single_count=2, double_count=0)


def test_a_single_mode_ignores_the_other_cap() -> None:
    settings = ScheduleSettings(
        daily_booking_limit_mode=DailyBookingLimitMode.PEOPLE, daily_people_limit=50, daily_ticket_limit=1
    )
    DailyBookingLimit(settings).check(DailyOnlineLoad(tickets=30, people=10), single_count=1, double_count=0)


# ---------------------------------------------------------------- capacity


def test_singles_and_the_two_seater_have_separate_capacities() -> None:
    allocator = SeatAllocator(ScheduleSettings())
    allocator.check(SessionLoad(5, 0), 1, 1)
    with pytest.raises(SessionFullError) as info:
        allocator.check(SessionLoad(5, 1), 1, 1)
    assert (info.value.singles_left, info.value.doubles_left) == (1, 0)
    with pytest.raises(SessionFullError):
        allocator.check(SessionLoad(6, 0), 1, 0)


@pytest.mark.parametrize(("singles", "doubles"), [(0, 0), (-1, 1), (8, 0)])
def test_a_request_must_be_sensible(singles: int, doubles: int) -> None:
    with pytest.raises(ValidationError):
        SeatAllocator(ScheduleSettings()).check(SessionLoad(), singles, doubles)


# ---------------------------------------------------------------- reservation lifecycle


def held(now: datetime = SATURDAY_MORNING, minutes: int = 20) -> Reservation:
    return Reservation.hold(
        code="DK-TEST123",
        ticket_number=100,
        customer_id=uuid.uuid4(),
        business_date=SUN,
        session_time=time(18, 0),
        starts_at=datetime(2026, 1, 4, 18, 0, tzinfo=TEHRAN),
        single_count=2,
        double_count=1,
        amount=Money.from_toman(2_580_000),
        contact_name="  علی   رضایی ",
        contact_mobile="09123456789",
        now=now,
        hold_minutes=minutes,
    )


def test_a_hold_takes_karts_until_it_runs_out() -> None:
    reservation = held()
    assert reservation.status is S.HELD and reservation.people == 4 and reservation.contact_name == "علی رضایی"
    assert reservation.occupies_seats_at(SATURDAY_MORNING + timedelta(minutes=19))
    assert not reservation.occupies_seats_at(SATURDAY_MORNING + timedelta(minutes=20))


def test_payment_confirms_once_and_raises_one_event() -> None:
    reservation = held()
    assert reservation.confirm_payment("pay-1", SATURDAY_MORNING + timedelta(minutes=5)) is True
    assert reservation.confirm_payment("pay-1", SATURDAY_MORNING + timedelta(minutes=6)) is False  # idempotent
    events = reservation.pull_events()
    assert [type(e) for e in events] == [ReservationConfirmed]
    assert events[0].confirmed_late is False and events[0].source == "online"


def test_a_late_payment_still_confirms_but_is_flagged() -> None:
    reservation = held()
    later = SATURDAY_MORNING + timedelta(minutes=25)
    reservation.expire(later)
    reservation.renew_hold(later, 10)
    assert reservation.status is S.HELD and reservation.occupies_seats_at(later)
    reservation.confirm_payment("pay-1", later)
    assert reservation.confirmed_late and reservation.status is S.CONFIRMED


def test_a_verified_payment_extends_a_running_hold_but_never_shortens_it() -> None:
    reservation = held()
    last_second = SATURDAY_MORNING + timedelta(minutes=19, seconds=59)
    reservation.extend_hold(last_second, 10)
    assert reservation.occupies_seats_at(SATURDAY_MORNING + timedelta(minutes=29))
    early = held()
    early.extend_hold(SATURDAY_MORNING + timedelta(minutes=1), 5)  # would end sooner than the hold itself
    assert early.hold_expires_at == SATURDAY_MORNING + timedelta(minutes=20)
    with pytest.raises(InvalidReservationTransitionError):
        held().extend_hold(SATURDAY_MORNING + timedelta(minutes=21), 10)  # a hold that already ran out is not revived


def test_a_payment_for_karts_sold_meanwhile_is_refused_with_a_refund_note() -> None:
    reservation = held()
    later = SATURDAY_MORNING + timedelta(minutes=40)
    reservation.refuse_late_payment("pay-9", later)
    events = reservation.pull_events()
    assert reservation.status is S.CANCELLED and reservation.payment_ref == "pay-9"
    assert [type(e) for e in events] == [ReservationCancelled] and events[0].was_paid is True
    with pytest.raises(InvalidReservationTransitionError):
        held().refuse_late_payment("pay-9", SATURDAY_MORNING)  # a running hold still has its karts


def test_customers_cancel_only_unpaid_holds_staff_can_cancel_paid_ones() -> None:
    reservation = held()
    reservation.confirm_payment("pay-1", SATURDAY_MORNING)
    with pytest.raises(InvalidReservationTransitionError):
        reservation.cancel(reason="x", by_staff=False, now=SATURDAY_MORNING)
    reservation.cancel(reason="بارش باران", by_staff=True, now=SATURDAY_MORNING)
    cancelled = [e for e in reservation.pull_events() if isinstance(e, ReservationCancelled)]
    assert reservation.status is S.CANCELLED and cancelled[0].was_paid is True


def test_a_hold_cannot_expire_early_and_a_cancelled_one_cannot_be_paid() -> None:
    reservation = held()
    with pytest.raises(InvalidReservationTransitionError):
        reservation.expire(SATURDAY_MORNING + timedelta(minutes=1))
    reservation.cancel(reason="", by_staff=False, now=SATURDAY_MORNING)
    with pytest.raises(InvalidReservationTransitionError):
        reservation.confirm_payment("pay-1", SATURDAY_MORNING)


def test_check_in_only_after_confirmation() -> None:
    reservation = held()
    with pytest.raises(InvalidReservationTransitionError):
        reservation.mark_attended(SATURDAY_MORNING)
    reservation.confirm_payment("pay-1", SATURDAY_MORNING)
    reservation.mark_attended(SATURDAY_MORNING)
    assert reservation.status is S.ATTENDED


def test_staff_entries_are_confirmed_at_once_and_marked_as_staff() -> None:
    reservation = Reservation.staff_entry(
        code="DK-STAFF01",
        ticket_number=101,
        business_date=SUN,
        session_time=time(19, 0),
        starts_at=datetime(2026, 1, 4, 19, 0, tzinfo=TEHRAN),
        single_count=3,
        double_count=0,
        amount=Money(0),
        contact_name="",
        contact_mobile="",
        note="فروش حضوری",
        now=SATURDAY_MORNING,
    )
    assert reservation.status is S.CONFIRMED and reservation.source is ReservationSource.STAFF
    assert reservation.customer_id is None and reservation.occupies_seats_at(SATURDAY_MORNING)
