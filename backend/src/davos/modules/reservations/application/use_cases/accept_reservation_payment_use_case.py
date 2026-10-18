from __future__ import annotations

import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.money import Money


class AcceptReservationPaymentUseCase:
    """Asked by the payment flow after the bank verified a payment and before the money is settled.

    Yes only when the reservation exists, belongs to the payer, costs exactly the verified amount and can still get
    its karts. When its hold already ran out, the karts are taken again under the session lock (if still free and
    the session has not started), so nothing can be sold in between. A "no" makes the payment flow give the money back.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        reservations: ReservationRepository,
        settings: ScheduleSettingsRepository,
        clock: Clock,
        hold_extension_minutes: int,
    ) -> None:
        self._uow = uow
        self._reservations = reservations
        self._settings = settings
        self._clock = clock
        # how long karts stay taken for a verified payment until it is recorded (also after the hold ran out)
        self._extension = hold_extension_minutes

    async def execute(self, reservation_id: uuid.UUID, customer_id: uuid.UUID, amount: Money) -> bool:
        now = self._clock.now()
        async with self._uow:
            reservation = await self._reservations.get_for_update(reservation_id)
            if reservation is None or reservation.customer_id != customer_id or reservation.amount != amount:
                return False
            if reservation.status is ReservationStatus.HELD and reservation.occupies_seats_at(now):
                # Still holding its karts: make sure it keeps them until the payment is recorded, even if that
                # happens after the original hold time (no session lock needed: the karts are already counted).
                reservation.extend_hold(now, self._extension)
                await self._reservations.save(reservation)
                await self._uow.commit()
                return True
            if reservation.status not in {ReservationStatus.HELD, ReservationStatus.EXPIRED}:
                return False
            if reservation.starts_at <= now:
                return False
            settings = await self._settings.get()
            await self._reservations.lock_session(reservation.business_date, reservation.session_time)
            load = await self._reservations.session_load(reservation.business_date, reservation.session_time, now)
            left = SeatAllocator(settings).remaining(load)
            if reservation.single_count > left.singles or reservation.double_count > left.doubles:
                return False
            reservation.renew_hold(now, self._extension)
            await self._reservations.save(reservation)
            await self._uow.commit()
            return True
