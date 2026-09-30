from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest

from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.errors.invalid_reservation_transition_error import (
    InvalidReservationTransitionError,
)
from davos.modules.reservations.domain.errors.session_full_error import SessionFullError
from davos.modules.reservations.domain.events.reservation_cancelled import ReservationCancelled
from davos.modules.reservations.domain.events.reservation_confirmed import ReservationConfirmed
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN, business_date
from davos.shared_kernel.domain.errors.validation_error import ValidationError
from davos.shared_kernel.domain.money import Money

SAT, SUN, WED, THU, FRI = date(2026, 1, 3), date(2026, 1, 4), date(2026, 1, 7), date(2026, 1, 8), date(2026, 1, 9)
SATURDAY_MORNING = datetime(2026, 1, 3, 9, 30, tzinfo=TEHRAN)
S = ReservationStatus


# ---------------------------------------------------------------- calendar


def test_default_sessions_run_every_15_minutes_from_15_to_01() -> None:
    times = SessionCalendar(ScheduleSettings()).session_times()
    assert times[0] == time(15, 0) and times[-1] == time(0, 45) and len(times) == 40


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


def test_same_day_booking_keeps_a_lead_time_before_the_session() -> None:
    settings = ScheduleSettings(min_days_ahead=0, same_day_lead_minutes=30)
    calendar = SessionCalendar(settings)
    now = datetime(2026, 1, 3, 17, 50, tzinfo=TEHRAN)
    assert not calendar.is_bookable(SAT, time(18, 15), now)
    assert calendar.is_bookable(SAT, time(18, 30), now)


def test_only_real_session_times_are_bookable() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert not calendar.is_bookable(SUN, time(18, 7), SATURDAY_MORNING)
    assert not calendar.is_bookable(SUN, time(12, 0), SATURDAY_MORNING)
    assert calendar.is_bookable(SUN, time(0, 45), SATURDAY_MORNING)


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
    ],
)
def test_invalid_settings_are_refused(bad: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ScheduleSettings(**bad)  # type: ignore[arg-type]


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
