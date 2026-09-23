from __future__ import annotations

import uuid

from sqlalchemy import select, update

from davos.modules.identity.adapters.persistence.customer_session_mapper import CustomerSessionMapper
from davos.modules.identity.adapters.persistence.customer_session_model import CustomerSessionModel
from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.domain.entities.customer_session import CustomerSession
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemySessionRepository(SessionRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, session: CustomerSession) -> None:
        self._uow.session.add(CustomerSessionMapper.to_model(session))
        await self._uow.session.flush()

    async def get_by_token_digest(self, token_digest: str) -> CustomerSession | None:
        result = await self._uow.session.execute(
            select(CustomerSessionModel).where(CustomerSessionModel.token_digest == token_digest)
        )
        model = result.scalar_one_or_none()
        return CustomerSessionMapper.to_domain(model) if model else None

    async def get_owned(self, session_id: uuid.UUID, user_id: uuid.UUID) -> CustomerSession | None:
        result = await self._uow.session.execute(
            select(CustomerSessionModel).where(
                CustomerSessionModel.id == session_id, CustomerSessionModel.user_id == user_id
            )
        )
        model = result.scalar_one_or_none()
        return CustomerSessionMapper.to_domain(model) if model else None

    async def list_for_user(self, user_id: uuid.UUID) -> list[CustomerSession]:
        result = await self._uow.session.execute(
            select(CustomerSessionModel)
            .where(CustomerSessionModel.user_id == user_id)
            .order_by(CustomerSessionModel.last_seen_at.desc())
            .limit(100)
        )
        return [CustomerSessionMapper.to_domain(m) for m in result.scalars()]

    async def save(self, session: CustomerSession) -> None:
        await self._uow.session.execute(
            update(CustomerSessionModel)
            .where(CustomerSessionModel.id == session.id)
            .values(last_seen_at=session.last_seen_at, revoked_at=session.revoked_at)
        )
