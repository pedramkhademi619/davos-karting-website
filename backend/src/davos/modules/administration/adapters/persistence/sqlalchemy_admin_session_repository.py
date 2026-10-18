from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select, update

from davos.modules.administration.adapters.persistence.admin_session_model import AdminSessionModel
from davos.modules.administration.application.ports.admin_session_repository import AdminSessionRepository
from davos.modules.administration.domain.entities.admin_session import AdminSession
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

M = AdminSessionModel


class SqlAlchemyAdminSessionRepository(AdminSessionRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, session: AdminSession) -> None:
        self._uow.session.add(
            M(
                id=session.id,
                admin_id=session.admin_id,
                token_digest=session.token_digest,
                created_at=session.created_at,
                expires_at=session.expires_at,
                last_seen_at=session.last_seen_at,
                revoked_at=session.revoked_at,
                ip_hint=session.ip_hint,
                user_agent=session.user_agent,
            )
        )
        await self._uow.session.flush()

    async def get_by_token_digest(self, digest: str) -> AdminSession | None:
        result = await self._uow.session.execute(select(M).where(M.token_digest == digest))
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return AdminSession(
            session_id=model.id,
            admin_id=model.admin_id,
            token_digest=model.token_digest,
            created_at=model.created_at,
            expires_at=model.expires_at,
            last_seen_at=model.last_seen_at,
            ip_hint=model.ip_hint,
            user_agent=model.user_agent,
            revoked_at=model.revoked_at,
        )

    async def save(self, session: AdminSession) -> None:
        await self._uow.session.execute(
            update(M).where(M.id == session.id).values(last_seen_at=session.last_seen_at, revoked_at=session.revoked_at)
        )

    async def revoke_all_for(self, admin_id: uuid.UUID, now: datetime) -> None:
        await self._uow.session.execute(
            update(M).where(M.admin_id == admin_id, M.revoked_at.is_(None)).values(revoked_at=now)
        )
