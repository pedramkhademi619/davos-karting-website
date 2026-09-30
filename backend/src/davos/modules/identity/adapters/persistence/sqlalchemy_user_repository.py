from __future__ import annotations

import uuid

from sqlalchemy import ColumnElement, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert

from davos.modules.identity.adapters.persistence.user_mapper import UserMapper
from davos.modules.identity.adapters.persistence.user_model import UserModel
from davos.modules.identity.application.ports.customer_page import CustomerPage
from davos.modules.identity.application.ports.user_repository import UserRepository
from davos.modules.identity.domain.entities.user import User
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from davos.shared_kernel.domain.digit_normalizer import DigitNormalizer


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

    async def save(self, user: User) -> None:
        await self._uow.session.execute(
            update(UserModel)
            .where(UserModel.id == user.id)
            .values(full_name=user.full_name, marketing_opt_in=user.marketing_opt_in, status=user.status.value)
        )

    async def search(self, *, text: str, offset: int, limit: int) -> CustomerPage:
        needle = DigitNormalizer.to_ascii(text.strip())
        where = self._text_filter(needle)
        total = (await self._uow.session.execute(select(func.count()).select_from(UserModel).where(where))).scalar_one()
        result = await self._uow.session.execute(
            select(UserModel)
            .where(where)
            .order_by(UserModel.created_at.desc())
            .offset(max(offset, 0))
            .limit(min(max(limit, 1), 200))
        )
        return CustomerPage(items=[UserMapper.to_domain(m) for m in result.scalars()], total=int(total))

    async def marketing_mobiles(self) -> list[MobileNumber]:
        result = await self._uow.session.execute(
            select(UserModel.mobile).where(UserModel.marketing_opt_in.is_(True), UserModel.status == "active")
        )
        return [MobileNumber(m) for m in result.scalars()]

    @staticmethod
    def _text_filter(needle: str):  # type: ignore[no-untyped-def]
        if not needle:
            return text("true")
        digits = needle.lstrip("0").lstrip("+")
        if digits.startswith("98"):
            digits = digits[2:]
        escaped = needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions: list[ColumnElement[bool]] = [UserModel.full_name.ilike(f"%{escaped}%", escape="\\")]
        if digits.isdigit():
            conditions.append(UserModel.mobile.contains(digits))
        return or_(*conditions)
