from __future__ import annotations

from davos.modules.reservations.application.ports.reservation_code_generator import ReservationCodeGenerator
from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.application.use_cases.staff_reservation_command import StaffReservationCommand
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.counter_payment_method import CounterPaymentMethod
from davos.modules.reservations.domain.errors.fuel_break_session_error import FuelBreakSessionError
from davos.modules.reservations.domain.errors.session_not_bookable_error import SessionNotBookableError
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.money import Money


class CreateStaffReservationUseCase:
    """Staff enter karts sold at the counter so the website cannot sell the same seats (no payment, no SMS).

    Not held to the owner's demand-shaping rules (the daily cap, the shift-start closing of online booking): those
    exist to leave room for the counter. The fuel-break minute is the one rule staff cannot override either -- the
    karts are physically being refuelled then.
    """

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
            if calendar.is_blocked(command.session_time):
                raise FuelBreakSessionError
            if not calendar.is_session_time(command.session_time):
                raise SessionNotBookableError
            await self._reservations.lock_session(command.day, command.session_time)
            # Never more than the karts that are left, counting every other ticket of the session (online and counter).
            load = await self._reservations.session_load(command.day, command.session_time, now)
            SeatAllocator(settings).check(load, command.single_count, command.double_count)
            shift_key = calendar.shift_key(command.day, command.session_time)
            reservation = Reservation.staff_entry(
                code=self._codes.new_code(),
                ticket_number=await self._reservations.next_ticket_number(shift_key),
                shift_key=shift_key,
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
                payment_method=command.payment_method if command.amount_irr > 0 else CounterPaymentMethod.NONE,
            )
            await self._reservations.add(reservation)
            self._uow.collect_events(reservation.pull_events())
            await self._uow.commit()
        return reservation
