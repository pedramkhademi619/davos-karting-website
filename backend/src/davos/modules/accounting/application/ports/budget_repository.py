from __future__ import annotations

import uuid
from abc import ABC, abstractmethod


class BudgetRepository(ABC):
    @abstractmethod
    async def set_amount(self, account_id: uuid.UUID, year: int, month: int, amount_irr: int) -> None:
        """Sets (or, for zero, removes) one account's budget for one Jalali month."""

    @abstractmethod
    async def for_year(self, year: int) -> dict[tuple[uuid.UUID, int], int]:
        """(account, month) -> budget in Rial."""
