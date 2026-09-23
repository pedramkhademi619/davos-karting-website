from enum import StrEnum


class QuickTopic(StrEnum):
    """Predictable questions whose answer is one published knowledge entry, so no model or cache is needed."""

    HOURS = "hours"
    BOOKING = "booking"
    CAPACITY = "capacity"
    PRICES = "prices"
    CLUB = "club"
