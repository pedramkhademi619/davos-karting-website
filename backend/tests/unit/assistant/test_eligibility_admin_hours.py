"""The assistant applies the admin panel's under-15 hours and morning shift, not fixed numbers."""

from __future__ import annotations

from datetime import time

from davos.modules.assistant.domain.services.eligibility_advisor import EligibilityAdvisor
from davos.modules.assistant.domain.value_objects.eligibility_rules import EligibilityRules
from davos.modules.assistant.domain.value_objects.party_facts import PartyFacts
from tests.fakes.standard_config import booking_facts


def advisor(**facts: object) -> EligibilityAdvisor:
    return EligibilityAdvisor(EligibilityRules().for_booking(booking_facts(**facts)))


def test_the_default_settings_keep_the_owners_rule() -> None:
    lines = " ".join(
        advisor().advise(PartyFacts(ages=(12,), height_cm=150, weekday=5, weekday_name="شنبه", at=time(16, 0)))
    )
    assert "شنبه تا چهارشنبه" in lines and "نتیجه: بله" in lines


def test_changed_days_and_hours_are_used() -> None:
    a = advisor(junior_weekdays=frozenset({3, 4}), junior_from=time(10, 0), junior_until=time(12, 0))
    thursday = " ".join(
        a.advise(PartyFacts(ages=(12,), height_cm=150, weekday=3, weekday_name="پنجشنبه", at=time(11, 0)))
    )
    assert "پنجشنبه، جمعه" in thursday and "نتیجه: بله" in thursday
    saturday = " ".join(a.advise(PartyFacts(ages=(12,), height_cm=150, weekday=5, weekday_name="شنبه", at=time(11, 0))))
    assert "نتیجه: نه" in saturday


def test_when_the_hours_bind_everyone_the_back_seat_is_bound_too() -> None:
    drivers_only = " ".join(advisor().advise(PartyFacts(ages=(7,), weekday=3, weekday_name="پنجشنبه")))
    assert "حضور زیر ۱۵ سال" not in drivers_only
    everyone = " ".join(advisor(junior_everyone=True).advise(PartyFacts(ages=(7,), weekday=3, weekday_name="پنجشنبه")))
    assert "حضور زیر ۱۵ سال" in everyone and "حتی روی صندلی عقب" in everyone and "مجاز نیست" in everyone


def test_the_morning_shift_answers_are_you_open() -> None:
    a = advisor(morning_shift=(time(9, 0), time(13, 0)))
    assert "نتیجه: بله" in a.advise(PartyFacts(at=time(10, 0), asks_if_open=True))[0]
    assert "بین شیفت صبح و شیفت عصر" in a.advise(PartyFacts(at=time(14, 0), asks_if_open=True))[0]
    plain = EligibilityAdvisor(EligibilityRules().for_booking(booking_facts(morning_shift=None)))
    assert "نتیجه: نه" in plain.advise(PartyFacts(at=time(10, 0), asks_if_open=True))[0]
