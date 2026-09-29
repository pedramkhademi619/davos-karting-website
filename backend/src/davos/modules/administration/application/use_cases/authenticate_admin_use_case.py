from __future__ import annotations

from davos.modules.administration.application.ports.admin_session_repository import AdminSessionRepository
from davos.modules.administration.application.ports.admin_token_service import AdminTokenService
from davos.modules.administration.application.ports.admin_user_repository import AdminUserRepository
from davos.modules.administration.application.use_cases.authenticated_admin import AuthenticatedAdmin
from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class AuthenticateAdminUseCase:
    """Resolve an admin cookie into an active staff member, or None."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        admins: AdminUserRepository,
        sessions: AdminSessionRepository,
        tokens: AdminTokenService,
        clock: Clock,
        security: AdminSecurityPolicy,
    ) -> None:
        self._uow = uow
        self._admins = admins
        self._sessions = sessions
        self._tokens = tokens
        self._clock = clock
        self._security = security

    async def execute(self, raw_token: str) -> AuthenticatedAdmin | None:
        if not raw_token or len(raw_token) > 200:
            return None
        now = self._clock.now()
        async with self._uow:
            session = await self._sessions.get_by_token_digest(self._tokens.digest(raw_token))
            if session is None or not session.is_active(now, self._security.idle_timeout):
                return None
            admin = await self._admins.get(session.admin_id)
            if admin is None or not admin.is_active:
                return None
            if session.touch(now):
                await self._sessions.save(session)
                await self._uow.commit()
            return AuthenticatedAdmin(admin.id, session.id, admin.username, admin.display_name, admin.role)
