from __future__ import annotations

import uuid

from sqlalchemy import exists, select, update

from davos.modules.accounting.adapters.persistence.account_model import AccountModel
from davos.modules.accounting.adapters.persistence.journal_line_model import JournalLineModel
from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_role import AccountRole
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

A = AccountModel


def _to_domain(m: AccountModel) -> Account:
    return Account(
        account_id=m.id,
        code=m.code,
        name=m.name,
        account_type=AccountType(m.type),
        parent_id=m.parent_id,
        is_group=m.is_group,
        role=AccountRole(m.role) if m.role else None,
        active=m.active,
        is_system=m.is_system,
        created_at=m.created_at,
    )


class SqlAlchemyAccountRepository(AccountRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, account: Account) -> None:
        self._uow.session.add(
            AccountModel(
                id=account.id,
                code=account.code,
                name=account.name,
                type=account.type.value,
                parent_id=account.parent_id,
                is_group=account.is_group,
                role=account.role.value if account.role else None,
                active=account.active,
                is_system=account.is_system,
                created_at=account.created_at,
            )
        )
        await self._uow.session.flush()

    async def save(self, account: Account) -> None:
        await self._uow.session.execute(
            update(A).where(A.id == account.id).values(code=account.code, name=account.name, active=account.active)
        )

    async def get(self, account_id: uuid.UUID) -> Account | None:
        model = await self._uow.session.get(A, account_id)
        return _to_domain(model) if model else None

    async def get_by_code(self, code: str) -> Account | None:
        result = await self._uow.session.execute(select(A).where(A.code == code))
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def list_all(self) -> list[Account]:
        result = await self._uow.session.execute(select(A).order_by(A.code))
        return [_to_domain(m) for m in result.scalars()]

    async def roles(self) -> dict[AccountRole, uuid.UUID]:
        result = await self._uow.session.execute(select(A.role, A.id).where(A.role.is_not(None)))
        return {AccountRole(role): account_id for role, account_id in result.all()}

    async def has_entries(self, account_id: uuid.UUID) -> bool:
        result = await self._uow.session.execute(select(exists().where(JournalLineModel.account_id == account_id)))
        return bool(result.scalar())

    async def has_children(self, account_id: uuid.UUID) -> bool:
        result = await self._uow.session.execute(select(exists().where(A.parent_id == account_id)))
        return bool(result.scalar())
