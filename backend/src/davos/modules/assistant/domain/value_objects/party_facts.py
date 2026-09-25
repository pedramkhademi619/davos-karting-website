from __future__ import annotations

from dataclasses import dataclass
from datetime import time


@dataclass(frozen=True)
class PartyFacts:
    """What a customer's message says about the people who want to ride. Everything is optional: nothing is guessed."""

    ages: tuple[int, ...] = ()
    height_cm: int | None = None
    weekday: int | None = None  # Python weekday number
    weekday_name: str = ""
    at: time | None = None
    weights_kg: tuple[int, ...] = ()
    group_size: int | None = None
    has_licence: bool | None = None
    mentions_two_seater: bool = False
    mentions_rear_seat: bool = False
    mentions_women: bool = False
    mentions_today: bool = False
    mentions_booking: bool = False
    adults_only: bool = False

    @property
    def is_empty(self) -> bool:
        return not (
            self.ages
            or self.height_cm
            or self.weekday is not None
            or self.at
            or self.weights_kg
            or self.group_size
            or self.mentions_two_seater
            or self.mentions_today
        )
