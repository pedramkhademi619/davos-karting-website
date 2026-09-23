from __future__ import annotations

from typing import TypeVar

from davos.shared_kernel.domain.domain_event import DomainEvent
from davos.shared_kernel.domain.entity import Entity

IdT = TypeVar("IdT")


class AggregateRoot(Entity[IdT]):
    """Consistency boundary that records the domain events it raised."""

    def __init__(self, entity_id: IdT) -> None:
        super().__init__(entity_id)
        self._pending_events: list[DomainEvent] = []

    def _raise(self, event: DomainEvent) -> None:
        self._pending_events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events, self._pending_events = self._pending_events, []
        return events
