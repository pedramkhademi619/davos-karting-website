from __future__ import annotations

import logging
import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.services.seat_allocator import SeatAllocator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ConfirmPaidReservationUseCase:
    """Called when a payment for a reservation was verified. Idempotent: the callback and the event may both call it.

    Never overbooks. Normally the reservation still holds its karts (accepting the payment extended the hold). If the
    confirmation arrives later than that (for example the worker was down), the karts are checked again under the
    session lock; when they were sold meanwhile the reservation is cancelled with a refund-due reason instead.
    """

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

    async def execute(self, reservation_id: uuid.UUID, payment_ref: str) -> ReservationStatus | None:
        now = self._clock.now()
        async with self._uow:
            reservation = await self._reservations.get_for_update(reservation_id)
            if reservation is None:
                logger.error("paid reservation %s does not exist", reservation_id)
                return None
            if reservation.status is ReservationStatus.CANCELLED:
                # The customer released the seats and then paid anyway (a second tab): staff must refund.
                logger.error(
                    "payment %s arrived for cancelled reservation %s; refund it", payment_ref, reservation.code
                )
                return reservation.status
            if reservation.status in {ReservationStatus.HELD, ReservationStatus.EXPIRED} and not (
                reservation.occupies_seats_at(now)
            ):
                settings = await self._settings.get()
                await self._reservations.lock_session(reservation.business_date, reservation.session_time)
                load = await self._reservations.session_load(reservation.business_date, reservation.session_time, now)
                left = SeatAllocator(settings).remaining(load)
                if reservation.single_count > left.singles or reservation.double_count > left.doubles:
                    reservation.refuse_late_payment(payment_ref, now)
                    await self._reservations.save(reservation)
                    self._uow.collect_events(reservation.pull_events())
                    await self._uow.commit()
                    logger.error(
                        "payment %s for reservation %s was recorded after its karts were sold; cancelled, refund due",
                        payment_ref,
                        reservation.code,
                    )
                    return reservation.status
            changed = reservation.confirm_payment(payment_ref, now)
            if changed:
                if reservation.confirmed_late:
                    logger.warning(
                        "reservation %s paid after its hold expired; karts were still free", reservation.code
                    )
                await self._reservations.save(reservation)
                self._uow.collect_events(reservation.pull_events())
                await self._uow.commit()
            return reservation.status
