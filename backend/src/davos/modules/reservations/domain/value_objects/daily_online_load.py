from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DailyOnlineLoad:
    """How much of the owner's optional daily cap today's online bookings have already used.

    ``tickets`` is the number of online reservations that occupy seats right now (any party size counts as one);
    ``people`` is their total head count (a single-seater counts 1, the two-seater's rear seat counts 2). Staff
    entries at the counter are never included: the cap exists to leave them room.
    """

    tickets: int
    people: int
