from __future__ import annotations

import logging
import uuid

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ConfirmPaidReservationUseCase:
    """Called when a payment for a reservation was verified. Idempotent: the callback and the event may both call it."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository, clock: Clock) -> None:
        self._uow = uow
        self._reservations = reservations
        self._clock = clock

    async def execute(self, reservation_id: uuid.UUID, payment_ref: str) -> ReservationStatus | None:
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
            changed = reservation.confirm_payment(payment_ref, self._clock.now())
            if changed:
                if reservation.confirmed_late:
                    logger.warning("reservation %s paid after its hold expired; check the session", reservation.code)
                await self._reservations.save(reservation)
                self._uow.collect_events(reservation.pull_events())
                await self._uow.commit()
            return reservation.status
