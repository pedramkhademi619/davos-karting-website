from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Collection
from datetime import date

from davos.modules.accounting.application.ports.account_ledger import AccountLedger
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.value_objects.account_balance import AccountBalance
from davos.modules.accounting.domain.value_objects.party_line import PartyLine
from davos.modules.accounting.domain.value_objects.revenue_day import RevenueDay
from davos.modules.accounting.domain.value_objects.sales_receipt import SalesReceipt


class LedgerQuery(ABC):
    """Read-side aggregates over the posted journal lines (reversed entries and their reversals both count, so they
    cancel out exactly)."""

    @abstractmethod
    async def balances(
        self, date_from: date | None, date_to: date, exclude_sources: Collection[EntrySource] = ()
    ) -> list[AccountBalance]:
        """Per account: the net before ``date_from`` (all of it up to ``date_to`` when None) and the movement within."""

    @abstractmethod
    async def account_ledger(
        self, account_ids: Collection[uuid.UUID], date_from: date, date_to: date
    ) -> AccountLedger: ...

    @abstractmethod
    async def party_lines(self, account_id: uuid.UUID, as_of: date) -> list[PartyLine]: ...

    @abstractmethod
    async def sales_receipts(self, date_from: date, date_to: date) -> list[SalesReceipt]: ...

    @abstractmethod
    async def revenue_by_day(self, date_from: date, date_to: date) -> list[RevenueDay]: ...
