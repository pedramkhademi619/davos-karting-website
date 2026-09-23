from __future__ import annotations

import uuid
from abc import ABC, abstractmethod

from davos.modules.identity.domain.entities.customer_session import CustomerSession


class SessionRepository(ABC):
    @abstractmethod
    async def add(self, session: CustomerSession) -> None: ...

    @abstractmethod
    async def get_by_token_digest(self, token_digest: str) -> CustomerSession | None: ...

    @abstractmethod
    async def get_owned(self, session_id: uuid.UUID, user_id: uuid.UUID) -> CustomerSession | None:
        """Ownership is part of the query so a foreign session id can never be loaded."""

    @abstractmethod
    async def list_for_user(self, user_id: uuid.UUID) -> list[CustomerSession]: ...

    @abstractmethod
    async def save(self, session: CustomerSession) -> None: ...
