from __future__ import annotations

from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.application.ports.session_token_service import SessionTokenService
from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.application.use_cases.authenticated_customer import AuthenticatedCustomer
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class AuthenticateSessionUseCase:
    """Resolve a raw session cookie value into an authenticated customer, or None."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        sessions: SessionRepository,
        users: UserRepository,
        tokens: SessionTokenService,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._sessions = sessions
        self._users = users
        self._tokens = tokens
        self._clock = clock

    async def execute(self, raw_token: str) -> AuthenticatedCustomer | None:
        if not raw_token:
            return None
        now = self._clock.now()
        async with self._uow:
            session = await self._sessions.get_by_token_digest(self._tokens.digest(raw_token))
            if session is None or not session.is_active(now):
                return None
            user = await self._users.get_by_id(session.user_id)
            if user is None or not user.can_sign_in:
                return None
            if session.touch(now):
                await self._sessions.save(session)
                await self._uow.commit()
            return AuthenticatedCustomer(user_id=user.id, session_id=session.id)
