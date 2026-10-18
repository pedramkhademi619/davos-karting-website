from __future__ import annotations

from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ExpireHoldsUseCase:
    """Marks holds whose time ran out as expired (they already stopped counting against capacity when they ran out)."""

    def __init__(self, *, uow: UnitOfWork, reservations: ReservationRepository, clock: Clock) -> None:
        self._uow = uow
        self._reservations = reservations
        self._clock = clock

    async def execute(self, *, batch: int = 200) -> int:
        now = self._clock.now()
        async with self._uow:
            ids = await self._reservations.list_overdue_holds(now, limit=batch)
        expired = 0
        for reservation_id in ids:
            async with self._uow:
                reservation = await self._reservations.get_for_update(reservation_id)
                if reservation is None or reservation.status is not ReservationStatus.HELD:
                    continue
                reservation.expire(now)
                await self._reservations.save(reservation)
                await self._uow.commit()
                expired += 1
        return expired
