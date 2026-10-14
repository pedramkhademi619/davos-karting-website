from __future__ import annotations

import uuid
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.vendor_repository import VendorRepository
from davos.modules.accounting.application.services.ledger_posting_service import LedgerPostingService
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.entities.journal_entry import JournalEntry
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.enums.entry_source import EntrySource
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.errors.invalid_amount_error import InvalidAmountError
from davos.modules.accounting.domain.errors.missing_system_account_error import MissingSystemAccountError
from davos.modules.accounting.domain.errors.vendor_not_found_error import VendorNotFoundError
from davos.modules.accounting.domain.value_objects.journal_line import JournalLine
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError

_MAX_IRR = 1_000_000_000_000_000  # 100 trillion toman: far beyond any real amount, keeps arithmetic safe


class BookkeepingUseCase:
    """The everyday entries, asked for in business words (an expense, money received, a transfer, paying a supplier)
    instead of debits and credits."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        accounts: AccountRepository,
        vendors: VendorRepository,
        posting: LedgerPostingService,
    ) -> None:
        self._uow = uow
        self._accounts = accounts
        self._vendors = vendors
        self._posting = posting

    @staticmethod
    def _amount(value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= _MAX_IRR:
            raise InvalidAmountError
        return value

    async def _account(self, account_id: uuid.UUID, *types: AccountType) -> Account:
        account = await self._accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError
        account.ensure_postable()
        if types and account.type not in types:
            raise ValidationError("نوع این حساب برای این عملیات مناسب نیست.", code="account_type_mismatch")
        return account

    async def _role(self, role: AccountRole) -> uuid.UUID:
        found = (await self._accounts.roles()).get(role)
        if found is None:
            raise MissingSystemAccountError
        return found

    async def record_expense(
        self,
        *,
        day: date,
        expense_account_id: uuid.UUID,
        amount_irr: int,
        vat_irr: int,
        paid_from_account_id: uuid.UUID | None,
        vendor_id: uuid.UUID | None,
        description: str,
        created_by: str,
    ) -> JournalEntry:
        """Paid now from a cash or bank account, or on credit (owed to the supplier)."""
        amount = self._amount(amount_irr)
        if not 0 <= vat_irr < amount:
            raise InvalidAmountError("مالیات باید کمتر از کل مبلغ باشد.")
        async with self._uow:
            expense = await self._account(expense_account_id, AccountType.EXPENSE, AccountType.ASSET)
            memo = description or expense.name
            lines = [JournalLine(expense.id, debit_irr=amount - vat_irr, memo=memo, party_id=vendor_id)]
            if vat_irr:
                lines.append(JournalLine(await self._role(AccountRole.VAT_RECEIVABLE), debit_irr=vat_irr, memo=memo))
            if paid_from_account_id is not None:
                source = await self._account(paid_from_account_id, AccountType.ASSET, AccountType.LIABILITY)
                lines.append(JournalLine(source.id, credit_irr=amount, memo=memo, party_id=vendor_id))
            else:
                if vendor_id is None or await self._vendors.get(vendor_id) is None:
                    raise VendorNotFoundError("برای هزینه نسیه، تامین‌کننده را انتخاب کنید.")
                lines.append(
                    JournalLine(
                        await self._role(AccountRole.PAYABLES), credit_irr=amount, memo=memo, party_id=vendor_id
                    )
                )
            entry = await self._posting.post(
                entry_date=day, description=memo, lines=lines, source=EntrySource.EXPENSE, created_by=created_by
            )
            await self._uow.commit()
        return entry

    async def record_income(
        self,
        *,
        day: date,
        revenue_account_id: uuid.UUID,
        amount_irr: int,
        vat_irr: int,
        deposit_account_id: uuid.UUID,
        description: str,
        created_by: str,
    ) -> JournalEntry:
        """Money received for something other than a ticket (sponsorship, snack bar, hiring the track...)."""
        amount = self._amount(amount_irr)
        if not 0 <= vat_irr < amount:
            raise InvalidAmountError("مالیات باید کمتر از کل مبلغ باشد.")
        async with self._uow:
            revenue = await self._account(revenue_account_id, AccountType.REVENUE)
            deposit = await self._account(deposit_account_id, AccountType.ASSET)
            memo = description or revenue.name
            lines = [
                JournalLine(deposit.id, debit_irr=amount, memo=memo),
                JournalLine(revenue.id, credit_irr=amount - vat_irr, memo=memo),
            ]
            if vat_irr:
                lines.append(JournalLine(await self._role(AccountRole.VAT_PAYABLE), credit_irr=vat_irr, memo=memo))
            entry = await self._posting.post(
                entry_date=day, description=memo, lines=lines, source=EntrySource.INCOME, created_by=created_by
            )
            await self._uow.commit()
        return entry

    async def transfer(
        self,
        *,
        day: date,
        from_account_id: uuid.UUID,
        to_account_id: uuid.UUID,
        amount_irr: int,
        description: str,
        created_by: str,
    ) -> JournalEntry:
        amount = self._amount(amount_irr)
        if from_account_id == to_account_id:
            raise ValidationError("حساب مبدا و مقصد نباید یکی باشد.", code="same_account")
        async with self._uow:
            source = await self._account(from_account_id, AccountType.ASSET)
            target = await self._account(to_account_id, AccountType.ASSET)
            memo = description or f"انتقال از {source.name} به {target.name}"
            entry = await self._posting.post(
                entry_date=day,
                description=memo,
                lines=[
                    JournalLine(target.id, debit_irr=amount, memo=memo),
                    JournalLine(source.id, credit_irr=amount, memo=memo),
                ],
                source=EntrySource.TRANSFER,
                created_by=created_by,
            )
            await self._uow.commit()
        return entry

    async def pay_vendor(
        self,
        *,
        day: date,
        vendor_id: uuid.UUID,
        from_account_id: uuid.UUID,
        amount_irr: int,
        description: str,
        created_by: str,
    ) -> JournalEntry:
        amount = self._amount(amount_irr)
        async with self._uow:
            vendor = await self._vendors.get(vendor_id)
            if vendor is None:
                raise VendorNotFoundError
            source = await self._account(from_account_id, AccountType.ASSET)
            memo = description or f"پرداخت به {vendor.name}"
            entry = await self._posting.post(
                entry_date=day,
                description=memo,
                lines=[
                    JournalLine(
                        await self._role(AccountRole.PAYABLES), debit_irr=amount, memo=memo, party_id=vendor_id
                    ),
                    JournalLine(source.id, credit_irr=amount, memo=memo),
                ],
                source=EntrySource.VENDOR_PAYMENT,
                created_by=created_by,
            )
            await self._uow.commit()
        return entry

    async def pay_customer_refund(
        self, *, day: date, from_account_id: uuid.UUID, amount_irr: int, description: str, created_by: str
    ) -> JournalEntry:
        """Pays out money owed back to a customer (clears the refunds-payable balance)."""
        amount = self._amount(amount_irr)
        async with self._uow:
            source = await self._account(from_account_id, AccountType.ASSET)
            memo = description or "پرداخت استرداد وجه به مشتری"
            entry = await self._posting.post(
                entry_date=day,
                description=memo,
                lines=[
                    JournalLine(await self._role(AccountRole.REFUNDS_PAYABLE), debit_irr=amount, memo=memo),
                    JournalLine(source.id, credit_irr=amount, memo=memo),
                ],
                source=EntrySource.TRANSFER,
                created_by=created_by,
            )
            await self._uow.commit()
        return entry
