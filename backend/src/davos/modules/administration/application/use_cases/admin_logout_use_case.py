from __future__ import annotations

from davos.modules.administration.application.ports.admin_session_repository import AdminSessionRepository
from davos.modules.administration.application.ports.admin_token_service import AdminTokenService
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class AdminLogoutUseCase:
    def __init__(
        self, *, uow: UnitOfWork, sessions: AdminSessionRepository, tokens: AdminTokenService, clock: Clock
    ) -> None:
        self._uow = uow
        self._sessions = sessions
        self._tokens = tokens
        self._clock = clock

    async def execute(self, raw_token: str) -> None:
        async with self._uow:
            session = await self._sessions.get_by_token_digest(self._tokens.digest(raw_token))
            if session is None:
                return
            session.revoke(self._clock.now())
            await self._sessions.save(session)
            await self._uow.commit()
