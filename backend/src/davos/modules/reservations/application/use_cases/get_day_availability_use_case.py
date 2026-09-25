from __future__ import annotations

from datetime import date

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.application.use_cases.day_availability import DayAvailability
from davos.modules.reservations.application.use_cases.session_availability import SessionAvailability
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class GetDayAvailabilityUseCase:
    """Every session of one business day with the karts still free (the cinema seat map)."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        reservations: ReservationRepository,
        settings: ScheduleSettingsRepository,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._reservations = reservations
        self._settings = settings
        self._clock = clock

    async def execute(self, day: date, *, for_staff: bool = False) -> DayAvailability:
        now = self._clock.now()
        async with self._uow:
            settings = await self._settings.get()
            loads = await self._reservations.day_loads(day, now)
        calendar = SessionCalendar(settings)
        allocator = SeatAllocator(settings)
        sessions = []
        for session_time in calendar.session_times():
            left = allocator.remaining(loads.get(session_time, SessionLoad()))
            bookable = calendar.is_bookable(day, session_time, now) and (left.singles + left.doubles) > 0
            sessions.append(
                SessionAvailability(
                    session_time=session_time,
                    starts_at=calendar.starts_at(day, session_time),
                    singles_left=left.singles,
                    doubles_left=left.doubles,
                    single_capacity=settings.single_capacity,
                    double_capacity=settings.double_capacity,
                    bookable=bookable or (for_staff and (left.singles + left.doubles) > 0),
                )
            )
        return DayAvailability(
            day=day,
            is_holiday=settings.is_holiday(day),
            is_closed=settings.is_closed(day),
            prices=settings.prices_for(day),
            sessions=sessions,
        )
