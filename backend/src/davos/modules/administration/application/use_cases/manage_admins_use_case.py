from __future__ import annotations

import uuid

from davos.modules.administration.application.ports.admin_session_repository import AdminSessionRepository
from davos.modules.administration.application.ports.admin_user_repository import AdminUserRepository
from davos.modules.administration.application.ports.password_hasher import PasswordHasher
from davos.modules.administration.domain.entities.admin_user import AdminUser
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.modules.administration.domain.errors.admin_login_failed_error import AdminLoginFailedError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.conflict_error import ConflictError
from davos.shared_kernel.domain.errors.not_found_error import NotFoundError


class ManageAdminsUseCase:
    """Staff accounts: bootstrap the first owner, add staff, disable them, change passwords."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        admins: AdminUserRepository,
        sessions: AdminSessionRepository,
        hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._admins = admins
        self._sessions = sessions
        self._hasher = hasher
        self._clock = clock

    async def ensure_bootstrap_owner(self, *, username: str, password: str) -> bool:
        """Create the first owner from configuration when there is no admin at all. Never touches existing accounts."""
        async with self._uow:
            if await self._admins.count() > 0:
                return False
            AdminUser.check_password_strength(password)
            owner = AdminUser.create(
                username=username,
                display_name="مدیر",
                password_hash=self._hasher.hash(password),
                role=AdminRole.OWNER,
                now=self._clock.now(),
            )
            await self._admins.add(owner)
            await self._uow.commit()
        return True

    async def list_all(self) -> list[AdminUser]:
        async with self._uow:
            return await self._admins.list_all()

    async def create(self, *, username: str, display_name: str, password: str, role: AdminRole) -> AdminUser:
        AdminUser.check_password_strength(password)
        admin = AdminUser.create(
            username=username,
            display_name=display_name,
            password_hash=self._hasher.hash(password),
            role=role,
            now=self._clock.now(),
        )
        async with self._uow:
            if await self._admins.get_by_username_for_update(admin.username) is not None:
                raise ConflictError("این نام کاربری قبلا ثبت شده است.", code="username_taken")
            await self._admins.add(admin)
            await self._uow.commit()
        return admin

    async def set_active(self, *, admin_id: uuid.UUID, active: bool, acting_admin_id: uuid.UUID) -> AdminUser:
        if admin_id == acting_admin_id and not active:
            raise ConflictError("نمی‌توانید حساب خودتان را غیرفعال کنید.", code="cannot_disable_self")
        async with self._uow:
            admin = await self._admins.get(admin_id)
            if admin is None:
                raise NotFoundError("کاربر یافت نشد.")
            admin.is_active = active
            await self._admins.save(admin)
            if not active:
                await self._sessions.revoke_all_for(admin.id, self._clock.now())
            await self._uow.commit()
        return admin

    async def change_own_password(self, *, admin_id: uuid.UUID, current: str, new: str) -> None:
        AdminUser.check_password_strength(new)
        async with self._uow:
            admin = await self._admins.get(admin_id)
            if admin is None or not self._hasher.verify(current, admin.password_hash):
                raise AdminLoginFailedError
            admin.password_hash = self._hasher.hash(new)
            await self._admins.save(admin)
            await self._uow.commit()
