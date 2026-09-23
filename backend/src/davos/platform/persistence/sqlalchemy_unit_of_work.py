from __future__ import annotations

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.platform.persistence.outbox_recorder import OutboxRecorder
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.domain_event import DomainEvent


class SqlAlchemyUnitOfWork(UnitOfWork):
    """One database transaction per use case; domain events reach the outbox atomically."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession], outbox: OutboxRecorder) -> None:
        self._session_factory = session_factory
        self._outbox = outbox
        self._session: AsyncSession | None = None
        self._events: list[DomainEvent] = []

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("UnitOfWork used outside of 'async with'")
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        self._events = []
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self.session
        try:
            await session.rollback()  # no-op after commit; discards anything left uncommitted
        finally:
            await session.close()
            self._session = None

    def collect_events(self, events: list[DomainEvent]) -> None:
        self._events.extend(events)

    async def commit(self) -> None:
        self._outbox.record(self.session, self._events)
        self._events = []
        await self.session.commit()

    async def rollback(self) -> None:
        self._events = []
        await self.session.rollback()
