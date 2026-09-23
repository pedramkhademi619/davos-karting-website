import uuid
from abc import ABC, abstractmethod

from davos.modules.payments.application.ports.order_quote import OrderQuote


class OrderQuotePort(ABC):
    """Source of trusted amounts. The client never sends a price; only an order reference."""

    @abstractmethod
    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        """Return the payable amount for an order this customer owns, or None if there is none."""
