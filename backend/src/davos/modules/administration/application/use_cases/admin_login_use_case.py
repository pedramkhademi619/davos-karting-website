from __future__ import annotations

from datetime import timedelta

from davos.modules.administration.application.ports.admin_session_repository import AdminSessionRepository
from davos.modules.administration.application.ports.admin_token_service import AdminTokenService
from davos.modules.administration.application.ports.admin_user_repository import AdminUserRepository
from davos.modules.administration.application.ports.password_hasher import PasswordHasher
from davos.modules.administration.application.use_cases.admin_login_result import AdminLoginResult
from davos.modules.administration.application.use_cases.authenticated_admin import AuthenticatedAdmin
from davos.modules.administration.domain.entities.admin_session import AdminSession
from davos.modules.administration.domain.entities.admin_user import AdminUser
from davos.modules.administration.domain.errors.admin_locked_error import AdminLockedError
from davos.modules.administration.domain.errors.admin_login_failed_error import AdminLoginFailedError
from davos.modules.administration.domain.value_objects.admin_security_policy import AdminSecurityPolicy
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.rate_limiter import RateLimiter
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.rate_limited_error import RateLimitedError


class AdminLoginUseCase:
    """Username + password sign-in for staff.

    Defences: a per-IP rate limit, a per-account lock after too many wrong passwords (both from the security policy),
    the same answer and the same work (a dummy hash check) for unknown usernames, and failed attempts committed before
    the error is returned.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        admins: AdminUserRepository,
        sessions: AdminSessionRepository,
        hasher: PasswordHasher,
        tokens: AdminTokenService,
        rate_limiter: RateLimiter,
        clock: Clock,
        session_lifetime: timedelta,
        security: AdminSecurityPolicy,
    ) -> None:
        self._uow = uow
        self._admins = admins
        self._sessions = sessions
        self._hasher = hasher
        self._tokens = tokens
        self._rate_limiter = rate_limiter
        self._clock = clock
        self._lifetime = session_lifetime
        self._security = security

    async def execute(self, *, username: str, password: str, client_ip: str, user_agent: str) -> AdminLoginResult:
        decision = await self._rate_limiter.hit(
            f"admin-login:ip:{client_ip}", limit=self._security.logins_per_ip_per_15_minutes, window_seconds=900
        )
        if not decision.allowed:
            raise RateLimitedError(
                "تعداد تلاش‌های ورود زیاد است. کمی بعد دوباره تلاش کنید.",
                retry_after_seconds=decision.retry_after_seconds,
            )
        now = self._clock.now()
        async with self._uow:
            admin = await self._admins.get_by_username_for_update(AdminUser.normalize_username(username))
            if admin is None or not admin.is_active:
                self._hasher.dummy_verify(password)
                raise AdminLoginFailedError
            if admin.is_locked_at(now):
                raise AdminLockedError(admin.seconds_locked(now))
            if not self._hasher.verify(password, admin.password_hash):
                admin.record_failed_login(now, self._security)
                await self._admins.save(admin)
                await self._uow.commit()
                raise AdminLoginFailedError

            admin.record_login(now)
            await self._admins.save(admin)
            token = self._tokens.new_token()
            session = AdminSession.start(
                admin_id=admin.id,
                token_digest=self._tokens.digest(token),
                now=now,
                lifetime=self._lifetime,
                ip_hint=client_ip,
                user_agent=user_agent,
            )
            await self._sessions.add(session)
            await self._uow.commit()
        return AdminLoginResult(
            token=token,
            expires_at=session.expires_at,
            admin=AuthenticatedAdmin(admin.id, session.id, admin.username, admin.display_name, admin.role),
        )
