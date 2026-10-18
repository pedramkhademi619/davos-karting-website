from __future__ import annotations

from enum import StrEnum


class JuniorScope(StrEnum):
    """Who the under-15 hours bind: only 11-14 year olds driving a single-seater (the owner's rule), or every
    under-15 on the track, back-seat passengers of a two-seater included."""

    DRIVERS = "drivers"
    EVERYONE = "everyone"
