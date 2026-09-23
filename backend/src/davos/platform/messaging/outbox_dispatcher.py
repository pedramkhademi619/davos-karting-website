from abc import ABC, abstractmethod

from davos.platform.messaging.outbox_envelope import OutboxEnvelope


class OutboxDispatcher(ABC):
    """Hands one committed event to the job system. Delivery is at-least-once, so consumers must be idempotent."""

    @abstractmethod
    async def dispatch(self, envelope: OutboxEnvelope) -> None: ...
