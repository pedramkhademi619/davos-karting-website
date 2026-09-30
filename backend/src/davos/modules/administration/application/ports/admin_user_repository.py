from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.administration.domain.entities.admin_user import AdminUser


class AdminUserRepository(ABC):
    @abstractmethod
    async def get(self, admin_id: uuid.UUID) -> AdminUser | None: ...

    @abstractmethod
    async def get_by_username_for_update(self, username: str) -> AdminUser | None: ...

    @abstractmethod
    async def add(self, admin: AdminUser) -> None: ...

    @abstractmethod
    async def save(self, admin: AdminUser) -> None: ...

    @abstractmethod
    async def list_all(self) -> list[AdminUser]: ...

    @abstractmethod
    async def count(self) -> int: ...
