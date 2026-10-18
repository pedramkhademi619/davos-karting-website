from __future__ import annotations

from davos.modules.assistant.application.ports.booking_facts_port import BookingFactsPort
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts


class FixedBookingFacts(BookingFactsPort):
    """Stands in for the live admin settings. The question set's expected numbers assume the admin panel's initial
    settings (ScheduleSettings defaults), which the CLI passes in."""

    def __init__(self, facts: BookingFacts) -> None:
        self._facts = facts

    async def current(self) -> BookingFacts:
        return self._facts
