from __future__ import annotations

import asyncio

from celery import Celery

from davos.platform.messaging.outbox_dispatcher import OutboxDispatcher
from davos.platform.messaging.outbox_envelope import OutboxEnvelope
from davos.worker.dispatcher_queues import DispatcherQueues

HANDLE_EVENT_TASK = "davos.events.handle"


class CeleryOutboxDispatcher(OutboxDispatcher):
    """Publishes outbox events as Celery tasks, choosing the queue from the event name."""

    _QUEUE_BY_PREFIX = (("notifications.", DispatcherQueues.SMS), ("assistant.", DispatcherQueues.AI))

    def __init__(self, celery_app: Celery) -> None:
        self._celery = celery_app

    def queue_for(self, event_name: str) -> str:
        return next(
            (q for prefix, q in self._QUEUE_BY_PREFIX if event_name.startswith(prefix)), DispatcherQueues.CRITICAL
        )

    async def dispatch(self, envelope: OutboxEnvelope) -> None:
        # send_task performs blocking network I/O: keep it off the event loop.
        await asyncio.to_thread(
            self._celery.send_task,
            HANDLE_EVENT_TASK,
            kwargs={
                "event_id": str(envelope.event_id),
                "event_name": envelope.event_name,
                "payload": envelope.payload,
            },
            queue=self.queue_for(envelope.event_name),
            task_id=str(envelope.event_id),  # duplicate publishes collapse to one task id
        )
