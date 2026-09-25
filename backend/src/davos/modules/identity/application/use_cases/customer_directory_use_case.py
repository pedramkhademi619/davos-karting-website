from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.customer_page import CustomerPage
from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.enums.user_status import UserStatus
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class CustomerDirectoryUseCase:
    """Admin view of customers: search, block/unblock, and the SMS news audience."""

    def __init__(self, *, uow: UnitOfWork, users: UserRepository) -> None:
        self._uow = uow
        self._users = users

    async def search(self, *, text: str = "", offset: int = 0, limit: int = 50) -> CustomerPage:
        async with self._uow:
            return await self._users.search(text=text, offset=offset, limit=limit)

    async def set_status(self, user_id: uuid.UUID, status: UserStatus) -> User:
        async with self._uow:
            user = await self._users.get_by_id(user_id)
            if user is None:
                raise NotFoundError("مشتری یافت نشد.")
            user.change_status(status)
            await self._users.save(user)
            await self._uow.commit()
        return user

    async def marketing_audience(self) -> list[MobileNumber]:
        async with self._uow:
            return await self._users.marketing_mobiles()
