from __future__ import annotations

import uuid

from sqlalchemy import func, select, update

from davos.modules.administration.adapters.persistence.admin_user_model import AdminUserModel
from davos.modules.administration.application.ports.admin_user_repository import AdminUserRepository
from davos.modules.administration.domain.entities.admin_user import AdminUser
from davos.modules.administration.domain.enums.admin_role import AdminRole
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

M = AdminUserModel


class SqlAlchemyAdminUserRepository(AdminUserRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get(self, admin_id: uuid.UUID) -> AdminUser | None:
        model = await self._uow.session.get(M, admin_id)
        return self._domain(model) if model else None

    async def get_by_username_for_update(self, username: str) -> AdminUser | None:
        result = await self._uow.session.execute(select(M).where(M.username == username).with_for_update())
        model = result.scalar_one_or_none()
        return self._domain(model) if model else None

    async def add(self, admin: AdminUser) -> None:
        self._uow.session.add(
            M(
                id=admin.id,
                username=admin.username,
                display_name=admin.display_name,
                password_hash=admin.password_hash,
                role=admin.role.value,
                is_active=admin.is_active,
                failed_attempts=admin.failed_attempts,
                locked_until=admin.locked_until,
                last_login_at=admin.last_login_at,
                created_at=admin.created_at,
            )
        )
        await self._uow.session.flush()

    async def save(self, admin: AdminUser) -> None:
        await self._uow.session.execute(
            update(M)
            .where(M.id == admin.id)
            .values(
                display_name=admin.display_name,
                password_hash=admin.password_hash,
                role=admin.role.value,
                is_active=admin.is_active,
                failed_attempts=admin.failed_attempts,
                locked_until=admin.locked_until,
                last_login_at=admin.last_login_at,
            )
        )

    async def list_all(self) -> list[AdminUser]:
        result = await self._uow.session.execute(select(M).order_by(M.created_at))
        return [self._domain(m) for m in result.scalars()]

    async def count(self) -> int:
        return int((await self._uow.session.execute(select(func.count()).select_from(M))).scalar_one())

    @staticmethod
    def _domain(model: AdminUserModel) -> AdminUser:
        return AdminUser(
            admin_id=model.id,
            username=model.username,
            display_name=model.display_name,
            password_hash=model.password_hash,
            role=AdminRole(model.role),
            is_active=model.is_active,
            created_at=model.created_at,
            failed_attempts=model.failed_attempts,
            locked_until=model.locked_until,
            last_login_at=model.last_login_at,
        )
