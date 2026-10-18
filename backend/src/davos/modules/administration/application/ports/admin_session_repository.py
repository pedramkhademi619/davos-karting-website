from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.administration.domain.entities.admin_session import AdminSession


class AdminSessionRepository(ABC):
    @abstractmethod
    async def add(self, session: AdminSession) -> None: ...

    @abstractmethod
    async def get_by_token_digest(self, digest: str) -> AdminSession | None: ...

    @abstractmethod
    async def save(self, session: AdminSession) -> None: ...

    @abstractmethod
    async def revoke_all_for(self, admin_id: uuid.UUID, now: datetime) -> None: ...
