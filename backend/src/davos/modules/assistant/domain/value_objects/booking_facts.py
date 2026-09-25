from __future__ import annotations

from dataclasses import dataclass

# Python weekday numbers (Monday = 0).
THURSDAY_AND_FRIDAY = frozenset({3, 4})


@dataclass(frozen=True)
class BookingFacts:
    """The owner's current booking settings, as the assistant needs them. They are edited in the admin panel, so the
    assistant reads them live instead of quoting numbers from a text file that would go stale.

    The defaults are only used when the settings cannot be read (they match the settings' own defaults).
    """

    singles_per_session: int = 6
    doubles_per_session: int = 1
    normal_single_toman: int = 790_000
    normal_double_toman: int = 1_000_000
    holiday_single_toman: int = 940_000
    holiday_double_toman: int = 1_200_000
    holiday_weekdays: frozenset[int] = THURSDAY_AND_FRIDAY
    closed_weekdays: frozenset[int] = THURSDAY_AND_FRIDAY
    online_booking_enabled: bool = True
    min_days_ahead: int = 1
    hold_minutes: int = 20
