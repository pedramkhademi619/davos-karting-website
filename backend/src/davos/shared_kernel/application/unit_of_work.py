from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from davos.shared_kernel.domain.domain_event import DomainEvent


class UnitOfWork(ABC):
    """Transaction boundary of one use case.

    Leaving the ``async with`` block without an explicit ``commit()`` rolls back, so a
    forgotten commit can never persist half-finished work.
    """

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...

    @abstractmethod
    def collect_events(self, events: list[DomainEvent]) -> None:
        """Queue domain events; they are written to the outbox atomically with ``commit()``."""
