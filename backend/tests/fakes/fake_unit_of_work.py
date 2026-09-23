from __future__ import annotations

from types import TracebackType
from typing import Self

from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.domain_event import DomainEvent


class FakeUnitOfWork(UnitOfWork):
    """Records commits and published events; leaving the block without commit counts as rollback."""

    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0
        self.published_events: list[DomainEvent] = []
        self._pending: list[DomainEvent] = []

    async def __aenter__(self) -> Self:
        self._pending = []
        return self

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        return None

    def collect_events(self, events: list[DomainEvent]) -> None:
        self._pending.extend(events)

    async def commit(self) -> None:
        self.commits += 1
        self.published_events.extend(self._pending)
        self._pending = []

    async def rollback(self) -> None:
        self.rollbacks += 1
        self._pending = []
