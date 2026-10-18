from __future__ import annotations

import uuid

from sqlalchemy import func, select, update

from davos.modules.accounting.adapters.persistence.depreciation_run_model import DepreciationRunModel
from davos.modules.accounting.adapters.persistence.fixed_asset_model import FixedAssetModel
from davos.modules.accounting.application.ports.fixed_asset_repository import FixedAssetRepository
from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset
from davos.modules.accounting.domain.enums.asset_status import AssetStatus
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

F = FixedAssetModel
D = DepreciationRunModel


def _to_domain(m: FixedAssetModel) -> FixedAsset:
    return FixedAsset(
        asset_id=m.id,
        name=m.name,
        asset_account_id=m.asset_account_id,
        cost_irr=m.cost_irr,
        salvage_irr=m.salvage_irr,
        in_service_date=m.in_service_date,
        life_months=m.life_months,
        status=AssetStatus(m.status),
        note=m.note,
        created_at=m.created_at,
    )


class SqlAlchemyFixedAssetRepository(FixedAssetRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, asset: FixedAsset) -> None:
        self._uow.session.add(
            FixedAssetModel(
                id=asset.id,
                name=asset.name,
                asset_account_id=asset.asset_account_id,
                cost_irr=asset.cost_irr,
                salvage_irr=asset.salvage_irr,
                in_service_date=asset.in_service_date,
                life_months=asset.life_months,
                status=asset.status.value,
                note=asset.note,
                created_at=asset.created_at,
            )
        )
        await self._uow.session.flush()

    async def save(self, asset: FixedAsset) -> None:
        await self._uow.session.execute(
            update(F).where(F.id == asset.id).values(name=asset.name, status=asset.status.value, note=asset.note)
        )

    async def get(self, asset_id: uuid.UUID) -> FixedAsset | None:
        model = await self._uow.session.get(F, asset_id)
        return _to_domain(model) if model else None

    async def list_all(self) -> list[FixedAsset]:
        result = await self._uow.session.execute(select(F).order_by(F.in_service_date, F.name))
        return [_to_domain(m) for m in result.scalars()]

    async def depreciated_total(self, asset_id: uuid.UUID) -> int:
        result = await self._uow.session.execute(
            select(func.coalesce(func.sum(D.amount_irr), 0)).where(D.asset_id == asset_id)
        )
        return int(result.scalar_one())

    async def depreciated_totals(self) -> dict[uuid.UUID, int]:
        result = await self._uow.session.execute(select(D.asset_id, func.sum(D.amount_irr)).group_by(D.asset_id))
        return {asset_id: int(total) for asset_id, total in result.all()}

    async def month_done(self, asset_id: uuid.UUID, month_key: str) -> bool:
        return await self._uow.session.get(D, (asset_id, month_key)) is not None

    async def record_depreciation(
        self, asset_id: uuid.UUID, month_key: str, amount_irr: int, entry_id: uuid.UUID
    ) -> None:
        self._uow.session.add(
            DepreciationRunModel(asset_id=asset_id, month_key=month_key, amount_irr=amount_irr, entry_id=entry_id)
        )
        await self._uow.session.flush()
