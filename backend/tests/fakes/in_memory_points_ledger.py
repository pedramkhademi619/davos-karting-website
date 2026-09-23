from __future__ import annotations

import uuid

from davos.modules.loyalty.application.ports.points_ledger_repository import PointsLedgerRepository
from davos.modules.loyalty.domain.entities.points_entry import PointsEntry
from davos.modules.loyalty.domain.enums.points_entry_kind import PointsEntryKind


class InMemoryPointsLedger(PointsLedgerRepository):
    def __init__(self) -> None:
        self.rows: list[PointsEntry] = []

    async def lock_account(self, customer_id: uuid.UUID) -> None:
        return None

    async def append(self, entry: PointsEntry) -> bool:
        if any(
            r.customer_id == entry.customer_id and r.kind is entry.kind and r.source_ref == entry.source_ref
            for r in self.rows
        ):
            return False
        self.rows.append(entry)
        return True

    async def entries(self, customer_id: uuid.UUID) -> list[PointsEntry]:
        return [r for r in self.rows if r.customer_id == customer_id]

    async def find(self, customer_id: uuid.UUID, kind: PointsEntryKind, source_ref: str) -> PointsEntry | None:
        return next(
            (r for r in self.rows if r.customer_id == customer_id and r.kind is kind and r.source_ref == source_ref),
            None,
        )
