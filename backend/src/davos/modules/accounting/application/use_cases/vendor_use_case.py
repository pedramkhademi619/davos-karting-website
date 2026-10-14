from __future__ import annotations

import uuid
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.ledger_query import LedgerQuery
from davos.modules.accounting.application.ports.vendor_repository import VendorRepository
from davos.modules.accounting.application.use_cases.vendor_with_balance import VendorWithBalance
from davos.modules.accounting.domain.entities.vendor import Vendor
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.errors.vendor_not_found_error import VendorNotFoundError
from davos.modules.accounting.domain.services.aging_calculator import AgingCalculator
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class VendorUseCase:
    def __init__(
        self,
        *,
        uow: UnitOfWork,
        vendors: VendorRepository,
        accounts: AccountRepository,
        ledger: LedgerQuery,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._vendors = vendors
        self._accounts = accounts
        self._ledger = ledger
        self._clock = clock

    async def list_with_balances(self, as_of: date) -> list[VendorWithBalance]:
        async with self._uow:
            vendors = await self._vendors.list_all()
            payables = (await self._accounts.roles()).get(AccountRole.PAYABLES)
            lines = await self._ledger.party_lines(payables, as_of) if payables else []
        balances = {b.party_id: b for b in AgingCalculator.age(lines, as_of)}
        return [VendorWithBalance(v, balances.get(v.id)) for v in vendors]

    async def create(self, *, name: str, phone: str, note: str) -> Vendor:
        async with self._uow:
            vendor = Vendor.create(name=name, phone=phone, note=note, now=self._clock.now())
            await self._vendors.add(vendor)
            await self._uow.commit()
        return vendor

    async def update(self, vendor_id: uuid.UUID, *, name: str, phone: str, note: str, active: bool) -> Vendor:
        async with self._uow:
            vendor = await self._vendors.get(vendor_id)
            if vendor is None:
                raise VendorNotFoundError
            vendor.edit(name=name, phone=phone, note=note, active=active)
            await self._vendors.save(vendor)
            await self._uow.commit()
        return vendor
