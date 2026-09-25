from __future__ import annotations

import time
from collections.abc import Callable

from davos.modules.assistant.application.ports.booking_facts_port import BookingFactsPort
from davos.modules.assistant.domain.value_objects.booking_facts import BookingFacts
from davos.modules.reservations.application.use_cases.schedule_settings_use_case import ScheduleSettingsUseCase
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings

_CACHE_SECONDS = 30.0


class ScheduleBookingFacts(BookingFactsPort):
    """Hands the assistant the booking settings the owner edits in the admin panel (kart counts, prices, booking days).

    Kept for a few seconds so a burst of questions reads the settings row once; a change in the admin panel reaches
    the assistant within ``_CACHE_SECONDS``. Lives in the composition layer so the two modules never import each other.
    """

    def __init__(self, settings: Callable[[], ScheduleSettingsUseCase]) -> None:
        self._settings = settings
        self._cached: BookingFacts | None = None
        self._read_at = 0.0

    async def current(self) -> BookingFacts:
        now = time.monotonic()
        if self._cached is None or now - self._read_at > _CACHE_SECONDS:
            self._cached = self.from_settings(await self._settings().get())
            self._read_at = now
        return self._cached

    @staticmethod
    def from_settings(s: ScheduleSettings) -> BookingFacts:
        return BookingFacts(
            singles_per_session=s.single_capacity,
            doubles_per_session=s.double_capacity,
            normal_single_toman=s.normal_prices.single.irr // 10,
            normal_double_toman=s.normal_prices.double.irr // 10,
            holiday_single_toman=s.holiday_prices.single.irr // 10,
            holiday_double_toman=s.holiday_prices.double.irr // 10,
            holiday_weekdays=s.holiday_weekdays,
            closed_weekdays=s.closed_weekdays,
            online_booking_enabled=s.online_booking_enabled,
            min_days_ahead=s.min_days_ahead,
            hold_minutes=s.hold_minutes,
        )
