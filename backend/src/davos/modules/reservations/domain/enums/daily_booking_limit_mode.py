from enum import StrEnum


class DailyBookingLimitMode(StrEnum):
    """How the owner optionally caps today's ONLINE bookings, to leave karts for walk-in customers.

    Staff entries at the counter are never counted against this cap -- that is exactly what it protects room for.
    """

    NONE = "none"  # no daily cap; each session's own capacity is the only limit
    PEOPLE = "people"  # at most N people total, counting single-seaters as 1 and the two-seater's rear seat as 2
    TICKETS = "tickets"  # at most N online reservations (tickets) today, whatever size each one is
    BOTH = "both"  # both caps at once: whichever is reached first closes online booking for the day
