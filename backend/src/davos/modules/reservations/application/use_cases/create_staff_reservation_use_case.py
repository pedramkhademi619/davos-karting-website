from __future__ import annotations

from davos.modules.reservations.application.ports.reservation_code_generator import ReservationCodeGenerator
from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.application.use_cases.staff_reservation_command import StaffReservationCommand
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.errors.session_not_bookable_error import SessionNotBookableError
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.money import Money


class CreateStaffReservationUseCase:
    """Staff enter karts sold at the counter so the website cannot sell the same seats (no payment, no SMS)."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        reservations: ReservationRepository,
        settings: ScheduleSettingsRepository,
        codes: ReservationCodeGenerator,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._reservations = reservations
        self._settings = settings
        self._codes = codes
        self._clock = clock

    async def execute(self, command: StaffReservationCommand) -> Reservation:
        now = self._clock.now()
        async with self._uow:
            settings = await self._settings.get()
            calendar = SessionCalendar(settings)
            if not calendar.is_session_time(command.session_time):
                raise SessionNotBookableError
            await self._reservations.lock_session(command.day, command.session_time)
            if not command.allow_overbooking:
                load = await self._reservations.session_load(command.day, command.session_time, now)
                SeatAllocator(settings).check(load, command.single_count, command.double_count)
            reservation = Reservation.staff_entry(
                code=self._codes.new_code(),
                business_date=command.day,
                session_time=command.session_time,
                starts_at=calendar.starts_at(command.day, command.session_time),
                single_count=command.single_count,
                double_count=command.double_count,
                amount=Money(max(command.amount_irr, 0)),
                contact_name=command.contact_name,
                contact_mobile=command.contact_mobile,
                note=command.note,
                now=now,
            )
            await self._reservations.add(reservation)
            self._uow.collect_events(reservation.pull_events())
            await self._uow.commit()
        return reservation
