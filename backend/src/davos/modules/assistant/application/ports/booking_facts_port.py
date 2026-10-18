from __future__ import annotations

from abc import ABC, abstractmethod

from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts


class BookingFactsPort(ABC):
    """The booking settings in force right now (kart counts, prices, closed days, hold time)."""

    @abstractmethod
    async def current(self) -> BookingFacts: ...
