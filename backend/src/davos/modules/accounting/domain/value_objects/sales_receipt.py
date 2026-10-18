from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SalesReceipt:
    """Money taken for tickets on one day, through one channel (the till, the card reader, the gateway...)."""

    day: date
    source: str
    role: str
    amount_irr: int
