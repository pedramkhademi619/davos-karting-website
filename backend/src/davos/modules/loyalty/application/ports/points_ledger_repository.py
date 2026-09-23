from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind


class PointsLedgerRepository(ABC):
    @abstractmethod
    async def lock_account(self, customer_id: uuid.UUID) -> None:
        """Serialise all point movements of one customer for the rest of the transaction."""

    @abstractmethod
    async def append(self, entry: PointsEntry) -> bool:
        """Append a line. False when (customer, kind, source_ref) already exists (idempotent replay)."""

    @abstractmethod
    async def entries(self, customer_id: uuid.UUID) -> list[PointsEntry]: ...

    @abstractmethod
    async def find(self, customer_id: uuid.UUID, kind: PointsEntryKind, source_ref: str) -> PointsEntry | None: ...
