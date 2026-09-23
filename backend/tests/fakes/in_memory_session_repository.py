from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.domain.entities.customer_session import CustomerSession


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.items: dict[uuid.UUID, CustomerSession] = {}

    async def add(self, session: CustomerSession) -> None:
        self.items[session.id] = session

    async def get_by_token_digest(self, token_digest: str) -> CustomerSession | None:
        return next((s for s in self.items.values() if s.token_digest == token_digest), None)

    async def get_owned(self, session_id: uuid.UUID, user_id: uuid.UUID) -> CustomerSession | None:
        session = self.items.get(session_id)
        return session if session and session.user_id == user_id else None

    async def list_for_user(self, user_id: uuid.UUID) -> list[CustomerSession]:
        return [s for s in self.items.values() if s.user_id == user_id]

    async def save(self, session: CustomerSession) -> None:
        self.items[session.id] = session
