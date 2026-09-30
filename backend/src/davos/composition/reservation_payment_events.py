from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from davos.composition.adapters.reservation_order_quote_port import ReservationOrderQuotePort
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.reservations.domain.enums.reservation_source import ReservationSource
from davos.modules.reservations.domain.enums.reservation_status import ReservationStatus
from davos.modules.reservations.domain.value_objects.tehran_time import local
from davos.shared_kernel.domain.jalali_date import JalaliDate

if TYPE_CHECKING:
    from davos.composition.application_container import ApplicationContainer

logger = logging.getLogger(__name__)

_PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


class ReservationPaymentEvents:
    """Reactions that cross module boundaries, run from the outbox (worker) and, for speed, from the payment callback.

    Every reaction is idempotent, because the same event can arrive from both paths or be retried by the queue.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        self._container = container

    async def handle(self, event_name: str, payload: dict[str, Any]) -> None:
        if event_name == "payments.PaymentSucceeded":
            await self.payment_succeeded(str(payload["order_ref"]), str(payload["payment_id"]))
        elif event_name == "payments.PaymentReversed" and payload.get("was_paid"):
            await self.paid_payment_reversed(str(payload["order_ref"]))
        elif event_name == "reservations.ReservationConfirmed" and payload.get("source") == ReservationSource.ONLINE:
            await self.send_confirmation_sms(uuid.UUID(str(payload["reservation_id"])))

    async def payment_succeeded(self, order_ref: str, payment_id: str) -> ReservationStatus | None:
        reservation_id = ReservationOrderQuotePort.reservation_id_of(order_ref)
        if reservation_id is None:
            return None
        return await self._container.confirm_paid_reservation().execute(reservation_id, payment_id)

    async def paid_payment_reversed(self, order_ref: str) -> None:
        reservation_id = ReservationOrderQuotePort.reservation_id_of(order_ref)
        if reservation_id is None:
            return
        reservation = await self._container.search_reservations().one(reservation_id)
        if reservation is None or reservation.status is not ReservationStatus.CONFIRMED:
            return
        await self._container.staff_update_reservation().cancel(reservation_id, "پرداخت توسط بانک برگشت خورد")

    async def send_confirmation_sms(self, reservation_id: uuid.UUID) -> None:
        reservation = await self._container.search_reservations().one(reservation_id)
        if reservation is None or not reservation.contact_mobile:
            return
        starts = local(reservation.starts_at)
        day = JalaliDate.from_gregorian(reservation.business_date)
        karts = []
        if reservation.single_count:
            karts.append(f"{reservation.single_count} خودرو تک‌نفره")
        if reservation.double_count:
            karts.append(f"{reservation.double_count} خودرو دونفره")
        parameters = {
            "name": reservation.contact_name,
            "ticket": reservation.code,
            "weekday": day.weekday_name,
            "date": day.numeric(),
            "time": starts.strftime("%H:%M").translate(_PERSIAN_DIGITS),
            "karts": " و ".join(karts).translate(_PERSIAN_DIGITS),
        }
        await self._container.send_transactional_sms().execute(
            SmsMessage(
                to_local_mobile=reservation.contact_mobile,
                template_key="reservation_confirmed",
                parameters=parameters,
                idempotency_key=f"reservation-confirmed:{reservation.id}",
            ),
            summary=f"تایید رزرو {reservation.code} - {day.numeric()} ساعت {self._clock_text(starts)}",
        )

    @staticmethod
    def _clock_text(moment: datetime) -> str:
        return moment.strftime("%H:%M").translate(_PERSIAN_DIGITS)
