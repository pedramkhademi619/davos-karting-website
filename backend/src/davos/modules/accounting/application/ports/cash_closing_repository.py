from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from davos.modules.accounting.domain.value_objects.cash_closing import CashClosing


class CashClosingRepository(ABC):
    @abstractmethod
    async def add(self, closing: CashClosing) -> None: ...

    @abstractmethod
    async def get(self, day: date) -> CashClosing | None: ...

    @abstractmethod
    async def recent(self, limit: int) -> list[CashClosing]: ...
