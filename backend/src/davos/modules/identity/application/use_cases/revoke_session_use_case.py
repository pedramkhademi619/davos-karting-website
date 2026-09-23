from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.domain.errors.session_not_found_error import SessionNotFoundError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class RevokeSessionUseCase:
    """Log a device out. Ownership is enforced in the repository query (IDOR-safe)."""

    def __init__(self, *, uow: UnitOfWork, sessions: SessionRepository, clock: Clock) -> None:
        self._uow = uow
        self._sessions = sessions
        self._clock = clock

    async def execute(self, *, user_id: uuid.UUID, session_id: uuid.UUID) -> None:
        async with self._uow:
            session = await self._sessions.get_owned(session_id, user_id)
            if session is None:
                raise SessionNotFoundError
            session.revoke(self._clock.now())
            await self._sessions.save(session)
            await self._uow.commit()
