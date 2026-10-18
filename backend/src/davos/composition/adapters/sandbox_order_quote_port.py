from __future__ import annotations

import re
import uuid

from davos.modules.payments.application.ports.order_quote import OrderQuote
from davos.modules.payments.application.ports.order_quote_port import OrderQuotePort
from davos.shared_kernel.domain.money import Money

_SANDBOX_ORDER = re.compile(r"sandbox-test-(\d{1,6})")
_SANDBOX_AMOUNT_IRR = 10_000


class SandboxOrderQuotePort(OrderQuotePort):
    """Controlled sandbox path: only order refs shaped ``sandbox-test-<n>`` are payable, for a fixed tiny amount.

    Enabled only outside production by PAYMENTS_SANDBOX_ORDERS_ENABLED. It invents no product or debt
    that a real customer could ever see: it exists so the payment flow can be exercised end to end.
    """

    async def quote(self, order_ref: str, customer_id: uuid.UUID) -> OrderQuote | None:
        if not _SANDBOX_ORDER.fullmatch(order_ref):
            return None
        return OrderQuote(amount=Money(_SANDBOX_AMOUNT_IRR), description="Sandbox test payment")

    async def accepts_payment(self, order_ref: str, customer_id: uuid.UUID, amount: Money) -> bool:
        return bool(_SANDBOX_ORDER.fullmatch(order_ref)) and amount == Money(_SANDBOX_AMOUNT_IRR)
