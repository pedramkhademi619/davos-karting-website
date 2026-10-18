from __future__ import annotations

import uuid

from sqlalchemy import select, update

from davos.modules.accounting.adapters.persistence.vendor_model import VendorModel
from davos.modules.accounting.application.ports.vendor_repository import VendorRepository
from davos.modules.accounting.domain.entities.vendor import Vendor
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _to_domain(m: VendorModel) -> Vendor:
    return Vendor(vendor_id=m.id, name=m.name, phone=m.phone, note=m.note, active=m.active, created_at=m.created_at)


class SqlAlchemyVendorRepository(VendorRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, vendor: Vendor) -> None:
        self._uow.session.add(
            VendorModel(
                id=vendor.id,
                name=vendor.name,
                phone=vendor.phone,
                note=vendor.note,
                active=vendor.active,
                created_at=vendor.created_at,
            )
        )
        await self._uow.session.flush()

    async def save(self, vendor: Vendor) -> None:
        await self._uow.session.execute(
            update(VendorModel)
            .where(VendorModel.id == vendor.id)
            .values(name=vendor.name, phone=vendor.phone, note=vendor.note, active=vendor.active)
        )

    async def get(self, vendor_id: uuid.UUID) -> Vendor | None:
        model = await self._uow.session.get(VendorModel, vendor_id)
        return _to_domain(model) if model else None

    async def list_all(self) -> list[Vendor]:
        result = await self._uow.session.execute(select(VendorModel).order_by(VendorModel.name))
        return [_to_domain(m) for m in result.scalars()]
