from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import time

from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts

# Python weekday numbers (Monday = 0): Saturday 5 ... Wednesday 2.
SATURDAY_TO_WEDNESDAY = frozenset({5, 6, 0, 1, 2})


@dataclass(frozen=True)
class EligibilityRules:
    """The owner's riding rules as numbers, so they are applied by code instead of being re-derived by a language model.

    The age, height, hour and weight rules are kept identical to backend/knowledge/single-seater.txt and two-seater.txt
    (a test checks the key numbers against those files). The under-15 days and hours are the owner's defaults; the admin
    panel can change them, and ``for_booking`` then applies the live values. The kart counts and booking days are not
    fixed here: they are the admin panel's booking settings, applied with ``for_booking``; until then they are unknown
    (None / empty) and the checks that need them say nothing rather than guess.
    """

    min_driving_age: int = 11  # under this never drives
    free_driving_age: int = 15  # from this age (15 included) a single-seater needs no height, day or hour condition
    junior_min_height_cm: int = 141  # 11 to 14 year olds need MORE than 140 cm
    junior_weekdays: frozenset[int] = SATURDAY_TO_WEDNESDAY
    junior_from: time = time(15, 0)
    junior_until: time = time(18, 0)
    # True when the admin panel applies the under-15 hours to every under-15, back-seat passengers included.
    junior_everyone: bool = False
    rear_seat_min_age: int = 4
    rear_seat_max_age: int = 14  # 15 and over count as grown-ups: they drive a single-seater, not the back seat
    front_seat_min_age: int = 18  # and a driving licence
    light_pair_max_total_kg: int = 130  # two light women: total strictly BELOW this
    opens_at: time = time(15, 0)  # opening hours, kept identical to backend/knowledge/working-hours.txt
    late_closing_weekdays: frozenset[int] = frozenset({3, 4})  # Thursday, Friday (and public holidays) close later
    late_closes_at: time = time(1, 0)  # on those days it is open until 01:00; on the others until 24:00
    morning_shift: tuple[time, time] | None = None  # from the admin panel: (opens, closes) of a morning shift
    # From the admin panel's booking settings (for_booking); unknown until then:
    singles_per_session: int | None = None
    doubles_per_session: int | None = None
    booking_closed_weekdays: frozenset[int] = frozenset()
    same_day_booking: bool | None = None
    normal_single_toman: int | None = None
    normal_double_toman: int | None = None
    holiday_single_toman: int | None = None
    holiday_double_toman: int | None = None
    holiday_weekdays: frozenset[int] = frozenset()

    def for_booking(self, facts: BookingFacts) -> EligibilityRules:
        return replace(
            self,
            singles_per_session=facts.singles_per_session,
            doubles_per_session=facts.doubles_per_session,
            booking_closed_weekdays=facts.closed_weekdays,
            same_day_booking=facts.min_days_ahead == 0,
            normal_single_toman=facts.normal_single_toman,
            normal_double_toman=facts.normal_double_toman,
            holiday_single_toman=facts.holiday_single_toman,
            holiday_double_toman=facts.holiday_double_toman,
            holiday_weekdays=facts.holiday_weekdays,
            junior_weekdays=facts.junior_weekdays if facts.junior_weekdays is not None else self.junior_weekdays,
            junior_from=facts.junior_from or self.junior_from,
            junior_until=facts.junior_until or self.junior_until,
            junior_everyone=facts.junior_everyone,
            morning_shift=facts.morning_shift,
        )
