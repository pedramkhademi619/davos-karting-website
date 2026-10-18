from __future__ import annotations

import uuid

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.errors.account_in_use_error import AccountInUseError
from davos.modules.accounting.domain.errors.account_not_found_error import AccountNotFoundError
from davos.modules.accounting.domain.errors.duplicate_account_code_error import DuplicateAccountCodeError
from davos.modules.accounting.domain.errors.system_account_error import SystemAccountError
from davos.modules.accounting.domain.services.default_chart import DEFAULT_CHART
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError


class ChartOfAccountsUseCase:
    """The chart of accounts (سرفصل‌ها): a tree whose leaves take entries. System accounts (those with a role) can be
    renamed and renumbered but never deleted or retyped, because automatic postings depend on them."""

    def __init__(self, *, uow: UnitOfWork, accounts: AccountRepository, clock: Clock) -> None:
        self._uow = uow
        self._accounts = accounts
        self._clock = clock

    async def list_all(self) -> list[Account]:
        async with self._uow:
            return await self._accounts.list_all()

    async def seed_default(self) -> int:
        """Creates the standard chart on a new installation; accounts that already exist (by code) are left alone."""
        created = 0
        async with self._uow:
            by_code = {a.code: a for a in await self._accounts.list_all()}
            for template in DEFAULT_CHART:
                if template.code in by_code:
                    continue
                parent = by_code[template.parent_code] if template.parent_code else None
                account = Account.create(
                    code=template.code,
                    name=template.name,
                    account_type=template.account_type,
                    parent_id=parent.id if parent else None,
                    is_group=template.is_group,
                    role=template.role,
                    is_system=template.role is not None,
                    now=self._clock.now(),
                )
                await self._accounts.add(account)
                by_code[account.code] = account
                created += 1
            await self._uow.commit()
        return created

    async def create(
        self, *, code: str, name: str, account_type: AccountType, parent_id: uuid.UUID | None, is_group: bool
    ) -> Account:
        async with self._uow:
            if await self._accounts.get_by_code(code.strip()) is not None:
                raise DuplicateAccountCodeError
            if parent_id is not None:
                parent = await self._accounts.get(parent_id)
                if parent is None:
                    raise AccountNotFoundError
                if not parent.is_group:
                    raise ValidationError("زیرحساب فقط زیر یک سرفصل گروه ساخته می‌شود.", code="parent_not_group")
                if parent.type is not account_type:
                    raise ValidationError("نوع حساب باید با نوع حساب والد یکی باشد.", code="parent_type_mismatch")
            account = Account.create(
                code=code,
                name=name,
                account_type=account_type,
                parent_id=parent_id,
                is_group=is_group,
                now=self._clock.now(),
            )
            await self._accounts.add(account)
            await self._uow.commit()
        return account

    async def update(self, account_id: uuid.UUID, *, code: str, name: str, active: bool) -> Account:
        async with self._uow:
            account = await self._accounts.get(account_id)
            if account is None:
                raise AccountNotFoundError
            other = await self._accounts.get_by_code(code.strip())
            if other is not None and other.id != account.id:
                raise DuplicateAccountCodeError
            if account.is_system and not active:
                raise SystemAccountError
            account.edit(code=code, name=name, active=active)
            await self._accounts.save(account)
            await self._uow.commit()
        return account

    async def delete(self, account_id: uuid.UUID) -> None:
        async with self._uow:
            account = await self._accounts.get(account_id)
            if account is None:
                raise AccountNotFoundError
            if account.is_system:
                raise SystemAccountError
            if await self._accounts.has_entries(account_id) or await self._accounts.has_children(account_id):
                raise AccountInUseError
            account.edit(code=account.code, name=account.name, active=False)
            await self._accounts.save(account)
            await self._uow.commit()
