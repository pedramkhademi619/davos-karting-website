from __future__ import annotations

from davos.modules.reservations.application.ports.reservation_code_generator import ReservationCodeGenerator
from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.application.use_cases.hold_reservation_command import HoldReservationCommand
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.daily_booking_limit_mode import DailyBookingLimitMode
from davos.modules.reservations.domain.errors.fuel_break_session_error import FuelBreakSessionError
from davos.modules.reservations.domain.errors.online_booking_closed_error import OnlineBookingClosedError
from davos.modules.reservations.domain.errors.online_booking_cutoff_passed_error import (
    OnlineBookingCutoffPassedError,
)
from davos.modules.reservations.domain.errors.session_not_bookable_error import SessionNotBookableError
from davos.modules.reservations.domain.errors.too_many_active_holds_error import TooManyActiveHoldsError
from davos.modules.reservations.domain.services.daily_booking_limit import DailyBookingLimit
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.modules.reservations.domain.services.session_calendar import SessionCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class HoldReservationUseCase:
    """Takes the chosen karts in a session for a few minutes while the customer pays.

    The session is locked for the length of the transaction and its load re-read under the lock, so two customers
    racing for the last kart cannot both get it. The optional daily cap is checked the same way, under its own,
    day-wide lock taken first (so the two locks can never deadlock against each other).
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

    async def execute(self, command: HoldReservationCommand) -> Reservation:
        now = self._clock.now()
        async with self._uow:
            settings = await self._settings.get()
            if not settings.online_booking_enabled:
                raise OnlineBookingClosedError
            calendar = SessionCalendar(settings)
            if calendar.is_online_cutoff_passed(now):
                assert settings.online_booking_cutoff is not None  # noqa: S101 - is_online_cutoff_passed confirmed it
                raise OnlineBookingCutoffPassedError(settings.online_booking_cutoff)
            if calendar.is_blocked(command.session_time):
                raise FuelBreakSessionError
            if not calendar.is_bookable(command.day, command.session_time, now):
                raise SessionNotBookableError
            active_holds = await self._reservations.count_active_holds(command.customer_id, now)
            if active_holds >= settings.max_active_holds_per_customer:
                raise TooManyActiveHoldsError

            if settings.daily_booking_limit_mode is not DailyBookingLimitMode.NONE:
                await self._reservations.lock_day(command.day)
                day_load = await self._reservations.day_online_load(command.day, now)
                DailyBookingLimit(settings).check(day_load, command.single_count, command.double_count)

            await self._reservations.lock_session(command.day, command.session_time)
            load = await self._reservations.session_load(command.day, command.session_time, now)
            SeatAllocator(settings).check(load, command.single_count, command.double_count)

            reservation = Reservation.hold(
                code=self._codes.new_code(),
                ticket_number=await self._reservations.next_ticket_number(),
                customer_id=command.customer_id,
                business_date=command.day,
                session_time=command.session_time,
                starts_at=calendar.starts_at(command.day, command.session_time),
                single_count=command.single_count,
                double_count=command.double_count,
                amount=settings.prices_for(command.day).total(command.single_count, command.double_count),
                contact_name=command.contact_name,
                contact_mobile=command.contact_mobile,
                now=now,
                hold_minutes=settings.hold_minutes,
            )
            await self._reservations.add(reservation)
            await self._uow.commit()
        return reservation
