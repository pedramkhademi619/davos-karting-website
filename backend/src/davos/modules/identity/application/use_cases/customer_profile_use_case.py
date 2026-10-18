from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.domain.entities.user import User
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class CustomerProfileUseCase:
    """The signed-in customer's own profile: name and SMS news consent."""

    def __init__(self, *, uow: UnitOfWork, users: UserRepository) -> None:
        self._uow = uow
        self._users = users

    async def get(self, user_id: uuid.UUID) -> User:
        async with self._uow:
            user = await self._users.get_by_id(user_id)
        if user is None:
            raise NotFoundError("حساب کاربری یافت نشد.")
        return user

    async def update(self, user_id: uuid.UUID, *, full_name: str, marketing_opt_in: bool) -> User:
        async with self._uow:
            user = await self._users.get_by_id(user_id)
            if user is None:
                raise NotFoundError("حساب کاربری یافت نشد.")
            user.update_profile(full_name=full_name, marketing_opt_in=marketing_opt_in)
            await self._users.save(user)
            await self._uow.commit()
        return user
