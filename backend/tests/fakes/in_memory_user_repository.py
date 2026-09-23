from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, User] = {}

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return self.items.get(user_id)

    async def get_by_mobile(self, mobile: MobileNumber) -> User | None:
        return next((u for u in self.items.values() if u.mobile == mobile), None)

    async def add_or_get(self, user: User) -> tuple[User, bool]:
        existing = await self.get_by_mobile(user.mobile)
        if existing:
            return existing, False
        self.items[user.id] = user
        return user, True
