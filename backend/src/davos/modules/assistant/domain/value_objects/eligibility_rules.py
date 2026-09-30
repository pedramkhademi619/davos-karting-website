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
    (a test checks the key numbers against those files). The kart counts and booking days are not fixed here: they are
    the admin panel's booking settings, applied with ``for_booking``; until then they are unknown (None / empty) and the
    checks that need them say nothing rather than guess.
    """

    min_driving_age: int = 11  # under this never drives
    unclear_age: int = 15  # exactly this age: coordinate with the counter
    free_driving_age: int = 16  # from this age a single-seater needs no height, day or hour condition
    junior_min_height_cm: int = 141  # 11 to 14 year olds need MORE than 140 cm
    junior_weekdays: frozenset[int] = SATURDAY_TO_WEDNESDAY
    junior_from: time = time(15, 0)
    junior_until: time = time(18, 0)
    rear_seat_min_age: int = 4
    rear_seat_max_age: int = 15
    front_seat_min_age: int = 18  # and a driving licence
    light_pair_max_total_kg: int = 130  # two light women: total strictly BELOW this
    # From the admin panel's booking settings (for_booking); unknown until then:
    singles_per_session: int | None = None
    doubles_per_session: int | None = None
    booking_closed_weekdays: frozenset[int] = frozenset()
    same_day_booking: bool | None = None

    def for_booking(self, facts: BookingFacts) -> EligibilityRules:
        return replace(
            self,
            singles_per_session=facts.singles_per_session,
            doubles_per_session=facts.doubles_per_session,
            booking_closed_weekdays=facts.closed_weekdays,
            same_day_booking=facts.min_days_ahead == 0,
        )
