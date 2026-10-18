from __future__ import annotations

import uuid

from davos.modules.payments.application.ports.order_quote import OrderQuote
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.shared_kernel.domain.money import Money


class FixedOrderQuotes(OrderQuotePort):
    """order_ref -> (owner, amount). Anything else is unknown, like a real order service."""

    def __init__(self) -> None:
        self.orders: dict[str, tuple[uuid.UUID, Money]] = {}
        self.refusing: set[str] = set()  # orders that no longer accept a payment (cancelled, expired...)
        self.acceptance_checks: list[str] = []

    def add(self, order_ref: str, owner: uuid.UUID, irr: int) -> None:
        self.orders[order_ref] = (owner, Money(irr))

    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        entry = self.orders.get(order_ref)
        if entry is None or entry[0] != customer_id:
            return None
        return OrderQuote(amount=entry[1], description=f"order {order_ref}")

    async def accepts_payment(self, order_ref: str, customer_id: uuid.UUID, amount: Money) -> bool:
        self.acceptance_checks.append(order_ref)
        entry = self.orders.get(order_ref)
        return entry is not None and entry == (customer_id, amount) and order_ref not in self.refusing
