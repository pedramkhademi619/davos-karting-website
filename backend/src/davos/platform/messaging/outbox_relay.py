from __future__ import annotations

import logging
import random
from collections.abc import Callable
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from davos.platform.messaging.outbox_dispatcher import OutboxDispatcher
from davos.platform.messaging.outbox_envelope import OutboxEnvelope
from davos.platform.messaging.relay_report import RelayReport
from davos.platform.persistence.outbox_message_model import OutboxMessageModel
from davos.shared_kernel.application.clock import Clock

logger = logging.getLogger(__name__)

_MAX_BACKOFF_SECONDS = 3600


class OutboxRelay:
    """Moves committed outbox rows to the job system.

    * Rows are claimed with ``FOR UPDATE SKIP LOCKED`` so any number of relay workers can run
      concurrently without dispatching the same row twice at the same time.
    * A failed dispatch is retried with exponential backoff and jitter; after ``max_attempts`` the row
      is dead-lettered (kept, flagged, visible to operators) instead of retried forever.
    * If the process dies after dispatching but before commit, the row is dispatched again:
      delivery is at-least-once and consumers deduplicate on ``event_id``.
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        dispatcher: OutboxDispatcher,
        clock: Clock,
        batch_size: int = 100,
        max_attempts: int = 8,
        base_backoff_seconds: float = 5.0,
        jitter: Callable[[], float] = random.random,
    ) -> None:
        self._session_factory = session_factory
        self._dispatcher = dispatcher
        self._clock = clock
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._base_backoff = base_backoff_seconds
        self._jitter = jitter

    def _backoff(self, attempts: int) -> timedelta:
        ceiling = min(self._base_backoff * (2 ** (attempts - 1)), _MAX_BACKOFF_SECONDS)
        return timedelta(seconds=ceiling * (0.5 + 0.5 * self._jitter()))

    async def run_once(self) -> RelayReport:
        now = self._clock.now()
        dispatched = failed = dead = 0
        async with self._session_factory() as session, session.begin():
            rows = (
                await session.execute(
                    select(OutboxMessageModel)
                    .where(
                        OutboxMessageModel.published_at.is_(None),
                        OutboxMessageModel.dead_lettered_at.is_(None),
                        OutboxMessageModel.available_at <= now,
                    )
                    .order_by(OutboxMessageModel.created_at)
                    .limit(self._batch_size)
                    .with_for_update(skip_locked=True)
                )
            ).scalars()
            for row in rows:
                try:
                    await self._dispatcher.dispatch(OutboxEnvelope(row.event_id, row.event_name, row.payload))
                except Exception as exc:
                    row.attempts += 1
                    row.last_error = type(exc).__name__  # never store provider messages that may hold PII
                    if row.attempts >= self._max_attempts:
                        row.dead_lettered_at = now
                        dead += 1
                        logger.error("outbox event dead-lettered event=%s attempts=%d", row.event_name, row.attempts)
                    else:
                        row.available_at = now + self._backoff(row.attempts)
                        failed += 1
                else:
                    row.published_at = now
                    dispatched += 1
        return RelayReport(dispatched=dispatched, failed=failed, dead_lettered=dead)
