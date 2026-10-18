from __future__ import annotations

import logging
import uuid
from datetime import date
from typing import TYPE_CHECKING, Any

from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus

if TYPE_CHECKING:
    from davos.composition.application_container import ApplicationContainer

logger = logging.getLogger(__name__)

_PAGE = 200


class AccountingEvents:
    """Keeps the books in step with reservations: a ticket that is paid or sold at the counter becomes a sale entry,
    a cancelled one becomes a refund entry. Every reaction is idempotent, because events can arrive twice."""

    def __init__(self, container: ApplicationContainer) -> None:
        self._container = container

    async def handle(self, event_name: str, payload: dict[str, Any]) -> None:
        if event_name == "reservations.ReservationConfirmed":
            await self.book_sale(uuid.UUID(str(payload["reservation_id"])))
        elif event_name == "reservations.ReservationCancelled":
            await self.book_refund(uuid.UUID(str(payload["reservation_id"])))

    async def book_sale(self, reservation_id: uuid.UUID) -> bool:
        reservation = await self._container.search_reservations().one(reservation_id)
        if reservation is None:
            return False
        return await self._post(reservation)

    async def _post(self, reservation: Reservation) -> bool:
        online = reservation.source is ReservationSource.ONLINE
        return await self._container.sales_posting().post_sale(
            reservation_id=str(reservation.id),
            amount_irr=reservation.amount.irr,
            online=online,
            counter_method=None if online else reservation.payment_method.value,
            session_day=reservation.business_date,
            label=f"فروش {'آنلاین' if online else 'حضوری'} بلیت {reservation.ticket_number}",
        )

    async def book_refund(self, reservation_id: uuid.UUID) -> None:
        reservation = await self._container.search_reservations().one(reservation_id)
        if reservation is None:
            return
        await self._container.sales_posting().refund_sale(
            reservation_id=str(reservation.id), label=f"استرداد بلیت {reservation.ticket_number}"
        )

    async def backfill(self, date_from: date, date_to: date) -> int:
        """Books every confirmed or attended reservation of the period that has no sale entry yet (e.g. from before the
        accounts were switched on). Returns how many entries were created."""
        created = 0
        for status in (ReservationStatus.CONFIRMED, ReservationStatus.ATTENDED):
            offset = 0
            while True:
                page = await self._container.search_reservations().execute(
                    ReservationQuery(date_from=date_from, date_to=date_to, status=status, offset=offset, limit=_PAGE)
                )
                for reservation in page.items:
                    if await self._post(reservation):
                        created += 1
                offset += _PAGE
                if offset >= page.total:
                    break
        return created
