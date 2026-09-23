from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from davos.platform.persistence.event_serializer import EventSerializer
from davos.platform.persistence.outbox_message_model import OutboxMessageModel
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.domain.domain_event import DomainEvent


class OutboxRecorder:
    def __init__(self, *, serializer: EventSerializer, clock: Clock) -> None:
        self._serializer = serializer
        self._clock = clock

    def record(self, session: AsyncSession, events: list[DomainEvent]) -> None:
        now = self._clock.now()
        for event in events:
            session.add(
                OutboxMessageModel(
                    event_id=event.event_id,
                    event_name=event.event_name,
                    payload=self._serializer.serialize(event),
                    occurred_at=event.occurred_at,
                    created_at=now,
                    available_at=now,
                )
            )
