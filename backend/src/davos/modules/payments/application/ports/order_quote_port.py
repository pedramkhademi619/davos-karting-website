import uuid
from abc import ABC, abstractmethod

from davos.modules.payments.application.ports.order_quote import OrderQuote
from davos.shared_kernel.domain.money import Money


class OrderQuotePort(ABC):
    """Source of trusted amounts. The client never sends a price; only an order reference."""

    @abstractmethod
    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        """Return the payable amount for an order this customer owns, or None if there is none."""

    @abstractmethod
    async def accepts_payment(self, order_ref: str, customer_id: uuid.UUID, amount: Money) -> bool:
        """Asked after the bank verified a payment and before it is settled: may this order still take exactly this
        amount from this customer? False means the money must go back (the order was cancelled, expired or changed)."""
