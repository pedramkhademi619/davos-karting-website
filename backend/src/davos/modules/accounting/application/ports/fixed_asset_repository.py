from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset


class FixedAssetRepository(ABC):
    @abstractmethod
    async def add(self, asset: FixedAsset) -> None: ...

    @abstractmethod
    async def save(self, asset: FixedAsset) -> None: ...

    @abstractmethod
    async def get(self, asset_id: uuid.UUID) -> FixedAsset | None: ...

    @abstractmethod
    async def list_all(self) -> list[FixedAsset]: ...

    @abstractmethod
    async def depreciated_total(self, asset_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def depreciated_totals(self) -> dict[uuid.UUID, int]: ...

    @abstractmethod
    async def month_done(self, asset_id: uuid.UUID, month_key: str) -> bool: ...

    @abstractmethod
    async def record_depreciation(
        self, asset_id: uuid.UUID, month_key: str, amount_irr: int, entry_id: uuid.UUID
    ) -> None: ...
