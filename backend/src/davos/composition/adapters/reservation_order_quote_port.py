from __future__ import annotations

import uuid
from collections.abc import Callable

from davos.modules.payments.application.ports.order_quote import OrderQuote
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.modules.reservations.application.use_cases.accept_reservation_payment_use_case import (
    AcceptReservationPaymentUseCase,
)
from davos.modules.reservations.application.use_cases.quote_reservation_use_case import QuoteReservationUseCase
from davos.shared_kernel.domain.money import Money

ORDER_PREFIX = "reservation:"


class ReservationOrderQuotePort(OrderQuotePort):
    """Bridges the payment module onto reservations: the only thing payable on the site is a held reservation.

    Order references look like ``reservation:<uuid>``. Lives in the composition layer so the two modules never import
    each other.
    """

    def __init__(
        self,
        quotes: Callable[[], QuoteReservationUseCase],
        acceptance: Callable[[], AcceptReservationPaymentUseCase],
    ) -> None:
        self._quotes = quotes
        self._acceptance = acceptance

    @staticmethod
    def order_ref_for(reservation_id: uuid.UUID) -> str:
        return f"{ORDER_PREFIX}{reservation_id}"

    @staticmethod
    def reservation_id_of(order_ref: str) -> uuid.UUID | None:
        if not order_ref.startswith(ORDER_PREFIX):
            return None
        try:
            return uuid.UUID(order_ref.removeprefix(ORDER_PREFIX))
        except ValueError:
            return None

    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        reservation_id = self.reservation_id_of(order_ref)
        if reservation_id is None:
            return None
        quote = await self._quotes().execute(reservation_id, customer_id)
        return OrderQuote(amount=quote.amount, description=quote.description) if quote else None

    async def accepts_payment(self, order_ref: str, customer_id: uuid.UUID, amount: Money) -> bool:
        reservation_id = self.reservation_id_of(order_ref)
        if reservation_id is None:
            return False
        return await self._acceptance().execute(reservation_id, customer_id, amount)
