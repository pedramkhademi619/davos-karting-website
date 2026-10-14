from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset


@dataclass(frozen=True)
class AssetWithBook:
    asset: FixedAsset
    accumulated_irr: int

    @property
    def book_value_irr(self) -> int:
        return self.asset.cost_irr - self.accumulated_irr
