"""The morning shift and the under-15 hours: both edited in the admin panel's booking settings."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, time

import pytest

from davos.api.schemas.schedule_settings_body import ScheduleSettingsBody
from davos.modules.reservations.adapters.persistence.schedule_settings_codec import ScheduleSettingsCodec
from davos.modules.reservations.domain.enums.junior_scope import JuniorScope
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.modules.reservations.domain.value_objects.tehran_time import TEHRAN
from davos.shared_kernel.domain.errors.validation_error import ValidationError

SATURDAY = date(2026, 10, 24)
THURSDAY = date(2026, 10, 22)
TWO_SHIFTS = ScheduleSettings(
    morning_shift_enabled=True,
    morning_start=time(9, 0),
    morning_end=time(10, 0),
    shift_start=time(15, 0),
    shift_end=time(16, 0),
    interval_minutes=20,
)


def test_without_a_morning_shift_the_grid_is_the_evening_alone() -> None:
    times = SessionCalendar(ScheduleSettings(morning_shift_enabled=False)).session_times()
    assert times[0] == time(15, 0) and time(10, 0) not in times and time(0, 50) in times


def test_by_default_the_morning_shift_starts_at_ten() -> None:
    times = SessionCalendar(ScheduleSettings()).session_times()
    assert times[0] == time(10, 0) and time(13, 50) in times and time(14, 0) not in times and time(15, 0) in times


def test_the_morning_shift_comes_first_on_the_same_business_day() -> None:
    calendar = SessionCalendar(TWO_SHIFTS)
    assert calendar.session_times() == [time(9, 0), time(9, 20), time(9, 40), time(15, 0), time(15, 20), time(15, 40)]
    assert calendar.starts_at(SATURDAY, time(9, 20)).date() == SATURDAY
    assert calendar.starts_at(SATURDAY, time(15, 0)).tzinfo == TEHRAN


def test_after_midnight_still_belongs_to_the_evening_before() -> None:
    calendar = SessionCalendar(ScheduleSettings())
    assert calendar.starts_at(SATURDAY, time(0, 30)).date() == date(2026, 10, 25)
    assert calendar.starts_at(SATURDAY, time(23, 30)).date() == SATURDAY


@pytest.mark.parametrize(
    "changes",
    [
        {"morning_shift_enabled": True, "morning_start": time(5, 0), "morning_end": time(9, 0)},  # before 06:00
        {
            "morning_shift_enabled": True,
            "morning_start": time(11, 0),
            "morning_end": time(10, 0),
        },  # ends before it starts
        {
            "morning_shift_enabled": True,
            "morning_start": time(9, 0),
            "morning_end": time(16, 0),
        },  # runs into the evening
        {"shift_start": time(4, 0), "shift_end": time(5, 0)},  # an evening shift cannot start before the day does
        {"shift_end": time(7, 0)},  # past midnight it must end by 06:00
        {"junior_from": time(18, 0), "junior_until": time(15, 0)},
        {"junior_weekdays": frozenset({9})},
    ],
)
def test_impossible_shifts_and_hours_are_refused(changes: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        replace(ScheduleSettings(), **changes)


def test_a_disabled_morning_shift_is_not_checked() -> None:
    settings = replace(
        ScheduleSettings(), morning_shift_enabled=False, morning_start=time(11, 0), morning_end=time(10, 0)
    )
    assert not settings.morning_shift_enabled


def test_the_under_fifteen_hours() -> None:
    s = ScheduleSettings()
    assert s.is_junior_time(SATURDAY, time(15, 0)) and s.is_junior_time(SATURDAY, time(17, 50))
    assert not s.is_junior_time(SATURDAY, time(18, 0)) and not s.is_junior_time(THURSDAY, time(16, 0))
    morning = replace(s, junior_weekdays=frozenset({3}), junior_from=time(9, 0), junior_until=time(12, 0))
    assert morning.is_junior_time(THURSDAY, time(10, 0)) and not morning.is_junior_time(SATURDAY, time(10, 0))


def test_the_codec_keeps_the_new_fields_and_old_rows_still_load() -> None:
    edited = replace(
        TWO_SHIFTS,
        junior_weekdays=frozenset({5, 6}),
        junior_from=time(9, 0),
        junior_until=time(10, 0),
        junior_scope=JuniorScope.EVERYONE,
    )
    assert ScheduleSettingsCodec.decode(ScheduleSettingsCodec.encode(edited)) == edited
    old_row = ScheduleSettingsCodec.encode(ScheduleSettings())
    for key in (
        "morning_shift_enabled",
        "morning_start",
        "morning_end",
        "junior_weekdays",
        "junior_from",
        "junior_until",
        "junior_scope",
    ):
        old_row.pop(key)
    assert ScheduleSettingsCodec.decode(old_row) == ScheduleSettings()


def test_the_admin_body_round_trips_and_older_clients_get_the_defaults() -> None:
    edited = replace(TWO_SHIFTS, junior_scope=JuniorScope.EVERYONE)
    assert ScheduleSettingsBody.of(edited).to_domain() == edited
    payload = ScheduleSettingsBody.of(ScheduleSettings()).model_dump()
    for key in (
        "morning_shift_enabled",
        "morning_start",
        "morning_end",
        "junior_weekdays",
        "junior_from",
        "junior_until",
        "junior_scope",
    ):
        payload.pop(key)
    assert ScheduleSettingsBody(**payload).to_domain() == ScheduleSettings()
