from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def get_by_mobile(self, mobile: MobileNumber) -> User | None: ...

    @abstractmethod
    async def add_or_get(self, user: User) -> tuple[User, bool]:
        """Insert the user, or return the existing one if the mobile was registered concurrently.

        Returns (user, created). Implementations must rely on the unique constraint on the
        mobile number, never on a check-then-insert sequence.
        """
