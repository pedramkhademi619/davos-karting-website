from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.accounting.domain.entities.account import Account
from davos.modules.accounting.domain.enums.account_role import AccountRole


class AccountRepository(ABC):
    @abstractmethod
    async def add(self, account: Account) -> None: ...

    @abstractmethod
    async def save(self, account: Account) -> None: ...

    @abstractmethod
    async def get(self, account_id: uuid.UUID) -> Account | None: ...

    @abstractmethod
    async def get_by_code(self, code: str) -> Account | None: ...

    @abstractmethod
    async def list_all(self) -> list[Account]: ...

    @abstractmethod
    async def roles(self) -> dict[AccountRole, uuid.UUID]:
        """The account that does each system job (cash, gateway, revenue...)."""

    @abstractmethod
    async def has_entries(self, account_id: uuid.UUID) -> bool: ...

    @abstractmethod
    async def has_children(self, account_id: uuid.UUID) -> bool: ...
