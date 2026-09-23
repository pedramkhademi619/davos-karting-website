from __future__ import annotations

import uuid

from davos.modules.identity.application.ports.session_repository import SessionRepository
from davos.modules.identity.application.use_cases.session_summary import SessionSummary
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ListSessionsUseCase:
    def __init__(self, *, uow: UnitOfWork, sessions: SessionRepository, clock: Clock) -> None:
        self._uow = uow
        self._sessions = sessions
        self._clock = clock

    async def execute(self, *, user_id: uuid.UUID, current_session_id: uuid.UUID) -> list[SessionSummary]:
        now = self._clock.now()
        async with self._uow:
            active = [s for s in await self._sessions.list_for_user(user_id) if s.is_active(now)]
        return [
            SessionSummary(
                session_id=s.id,
                user_agent=s.user_agent,
                ip_hint=s.ip_hint,
                created_at=s.created_at,
                last_seen_at=s.last_seen_at,
                is_current=s.id == current_session_id,
            )
            for s in sorted(active, key=lambda s: s.last_seen_at, reverse=True)
        ]
