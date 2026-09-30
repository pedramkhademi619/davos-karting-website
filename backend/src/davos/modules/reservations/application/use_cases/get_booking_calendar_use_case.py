from __future__ import annotations

from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.application.use_cases.bookable_day import BookableDay
from davos.modules.reservations.application.use_cases.booking_calendar import BookingCalendar
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetBookingCalendarUseCase:
    """The days a customer can book right now, with their prices."""

    def __init__(self, *, uow: UnitOfWork, settings: ScheduleSettingsRepository, clock: Clock) -> None:
        self._uow = uow
        self._settings = settings
        self._clock = clock

    async def execute(self) -> BookingCalendar:
        async with self._uow:
            settings = await self._settings.get()
        days = SessionCalendar(settings).bookable_dates(self._clock.now()) if settings.online_booking_enabled else []
        return BookingCalendar(
            online_booking_enabled=settings.online_booking_enabled,
            days=[BookableDay(day=d, is_holiday=settings.is_holiday(d), prices=settings.prices_for(d)) for d in days],
            hold_minutes=settings.hold_minutes,
            max_karts_per_reservation=settings.max_karts_per_reservation,
        )
