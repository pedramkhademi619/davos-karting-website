from __future__ import annotations

import uuid
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.fixed_asset_repository import FixedAssetRepository
from davos.modules.accounting.application.ports.vendor_repository import VendorRepository
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.application.use_cases.asset_with_book import AssetWithBook
from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.enums.asset_status import AssetStatus
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.errors.asset_not_found_error import AssetNotFoundError
from davos.modules.accounting.domain.errors.missing_system_account_error import MissingSystemAccountError
from davos.modules.accounting.domain.errors.vendor_not_found_error import VendorNotFoundError
from davos.modules.accounting.domain.services.depreciation_calculator import DepreciationCalculator
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class FixedAssetUseCase:
    """Karts and other equipment: registration (with the purchase entry), monthly depreciation, and disposal."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        assets: FixedAssetRepository,
        accounts: AccountRepository,
        vendors: VendorRepository,
        posting: LedgerPostingService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._assets = assets
        self._accounts = accounts
        self._vendors = vendors
        self._posting = posting
        self._clock = clock

    async def list_all(self) -> list[AssetWithBook]:
        async with self._uow:
            assets = await self._assets.list_all()
            totals = await self._assets.depreciated_totals()
        return [AssetWithBook(a, totals.get(a.id, 0)) for a in assets]

    async def register(
        self,
        *,
        name: str,
        asset_account_id: uuid.UUID,
        cost_irr: int,
        salvage_irr: int,
        in_service_date: date,
        life_months: int,
        note: str,
        paid_from_account_id: uuid.UUID | None,
        vendor_id: uuid.UUID | None,
        post_purchase: bool,
        created_by: str,
    ) -> FixedAsset:
        """With ``post_purchase`` the purchase is booked (paid from an account, or owed to a supplier); without it the
        asset is only registered, e.g. when its cost is already in the opening balances."""
        async with self._uow:
            account = await self._accounts.get(asset_account_id)
            if account is None:
                raise AccountNotFoundError
            if account.type is not AccountType.ASSET:
                raise ValidationError("حساب دارایی باید از نوع دارایی باشد.", code="account_type_mismatch")
            asset = FixedAsset.register(
                name=name,
                asset_account_id=asset_account_id,
                cost_irr=cost_irr,
                salvage_irr=salvage_irr,
                in_service_date=in_service_date,
                life_months=life_months,
                note=note,
                now=self._clock.now(),
            )
            await self._assets.add(asset)
            if post_purchase:
                memo = f"خرید دارایی: {asset.name}"
                lines = [JournalLine(asset_account_id, debit_irr=cost_irr, memo=memo, party_id=vendor_id)]
                if paid_from_account_id is not None:
                    source = await self._accounts.get(paid_from_account_id)
                    if source is None:
                        raise AccountNotFoundError
                    lines.append(JournalLine(source.id, credit_irr=cost_irr, memo=memo, party_id=vendor_id))
                else:
                    if vendor_id is None or await self._vendors.get(vendor_id) is None:
                        raise VendorNotFoundError("برای خرید نسیه، تامین‌کننده را انتخاب کنید.")
                    payables = (await self._accounts.roles()).get(AccountRole.PAYABLES)
                    if payables is None:
                        raise MissingSystemAccountError
                    lines.append(JournalLine(payables, credit_irr=cost_irr, memo=memo, party_id=vendor_id))
                await self._posting.post(
                    entry_date=in_service_date,
                    description=memo,
                    lines=lines,
                    source=EntrySource.ASSET_PURCHASE,
                    source_ref=str(asset.id),
                    created_by=created_by,
                )
            await self._uow.commit()
        return asset

    async def dispose(self, asset_id: uuid.UUID) -> None:
        async with self._uow:
            asset = await self._assets.get(asset_id)
            if asset is None:
                raise AssetNotFoundError
            asset.dispose()
            await self._assets.save(asset)
            await self._uow.commit()

    async def run_depreciation(self, year: int, month: int, *, created_by: str) -> int:
        """Books one month's depreciation for each active asset not yet done; returns the total (Rial)."""
        if not 1 <= month <= 12:
            raise ValidationError("ماه معتبر نیست.", code="invalid_month")
        month_key = FiscalCalendar.month_key(year, month)
        async with self._uow:
            roles = await self._accounts.roles()
            expense = roles.get(AccountRole.DEPRECIATION_EXPENSE)
            accumulated = roles.get(AccountRole.ACCUMULATED_DEPRECIATION)
            if expense is None or accumulated is None:
                raise MissingSystemAccountError
            todo: list[tuple[FixedAsset, int]] = []
            for asset in await self._assets.list_all():
                if asset.status is not AssetStatus.ACTIVE or await self._assets.month_done(asset.id, month_key):
                    continue
                amount = DepreciationCalculator.amount_for_month(
                    asset, year, month, await self._assets.depreciated_total(asset.id)
                )
                if amount > 0:
                    todo.append((asset, amount))
            total = sum(amount for _, amount in todo)
            if total == 0:
                return 0
            memo = f"استهلاک ماه {month_key}"
            entry = await self._posting.post(
                entry_date=FiscalCalendar.month_end(year, month),
                description=memo,
                lines=[
                    JournalLine(expense, debit_irr=total, memo=memo),
                    JournalLine(accumulated, credit_irr=total, memo=memo),
                ],
                source=EntrySource.DEPRECIATION,
                source_ref=month_key,
                created_by=created_by,
            )
            for asset, amount in todo:
                await self._assets.record_depreciation(asset.id, month_key, amount, entry.id)
            await self._uow.commit()
        return total
