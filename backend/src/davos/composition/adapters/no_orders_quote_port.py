from __future__ import annotations

import uuid

from davos.modules.payments.application.ports.order_quote import OrderQuote
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort


class NoOrdersQuotePort(OrderQuotePort):
    """Default: no order source is connected, so nothing is payable.

    Booking payments stay in the existing booking system; this port is replaced by a real
    order contract only when main-site payments are activated (see docs/INTEGRATIONS.md).
    """

    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        return None
