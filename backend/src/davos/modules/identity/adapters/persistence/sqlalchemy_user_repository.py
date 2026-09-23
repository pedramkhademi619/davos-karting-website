from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from davos.modules.identity.adapters.persistence.user_mapper import UserMapper
from davos.modules.identity.adapters.persistence.user_model import UserModel
from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        model = await self._uow.session.get(UserModel, user_id)
        return UserMapper.to_domain(model) if model else None

    async def get_by_mobile(self, mobile: MobileNumber) -> User | None:
        result = await self._uow.session.execute(select(UserModel).where(UserModel.mobile == mobile.e164))
        model = result.scalar_one_or_none()
        return UserMapper.to_domain(model) if model else None

    async def add_or_get(self, user: User) -> tuple[User, bool]:
        session = self._uow.session
        statement = (
            insert(UserModel)
            .values(id=user.id, mobile=user.mobile.e164, status=user.status.value, created_at=user.created_at)
            .on_conflict_do_nothing(index_elements=[UserModel.mobile])
            .returning(UserModel.id)
        )
        inserted_id = (await session.execute(statement)).scalar_one_or_none()
        if inserted_id is not None:
            return user, True
        existing = await self.get_by_mobile(user.mobile)
        if existing is None:  # pragma: no cover - only reachable if the row vanished between statements
            raise RuntimeError("user disappeared after conflicting insert")
        return existing, False
