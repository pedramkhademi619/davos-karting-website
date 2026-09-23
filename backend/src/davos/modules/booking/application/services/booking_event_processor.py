from __future__ import annotations

import logging

from davos.modules.booking.application.ports.booking_record_repository import BookingRecordRepository
from davos.modules.booking.application.ports.inbox_status import InboxStatus
from davos.modules.booking.application.ports.webhook_inbox_repository import WebhookInboxRepository
from davos.modules.booking.application.services.webhook_outcome import WebhookOutcome
from davos.modules.booking.domain.entities.booking_record import BookingRecord
from davos.modules.booking.domain.enums.apply_result import ApplyResult
from davos.modules.booking.domain.value_objects.booking_event import BookingEvent
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.domain_error import DomainError

logger = logging.getLogger(__name__)


class BookingEventProcessor:
    """Applies one verified event exactly once, atomically with its outbox events.

    Duplicate delivery is recognised through the inbox (unique event id). Stale (out-of-order)
    events are recorded as processed but change nothing. If processing fails, the whole transaction
    rolls back and the event is stored as FAILED in a separate transaction for later reprocessing.
    """

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        inbox: WebhookInboxRepository,
        records: BookingRecordRepository,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._inbox = inbox
        self._records = records
        self._clock = clock

    async def process(self, event: BookingEvent, body: str) -> WebhookOutcome:
        try:
            return await self._apply(event, body)
        except Exception as exc:
            code = exc.code if isinstance(exc, DomainError) else "processing_error"
            logger.warning("booking event %s failed: %s", event.event_id, code)
            async with self._uow:
                await self._inbox.mark_failed(event.event_id, body, code, self._clock.now())
                await self._uow.commit()
            raise

    async def _apply(self, event: BookingEvent, body: str) -> WebhookOutcome:
        now = self._clock.now()
        async with self._uow:
            previous = await self._inbox.register(event.event_id, body, now)
            if previous is InboxStatus.PROCESSED:
                return WebhookOutcome.DUPLICATE

            record = await self._records.get_for_update(event.external_booking_id)
            if record is None:
                record = BookingRecord.from_event(event, now)
                await self._records.add(record)
                outcome = WebhookOutcome.ACCEPTED
            else:
                applied = record.apply(event, now)
                await self._records.save(record)
                outcome = WebhookOutcome.ACCEPTED if applied is ApplyResult.APPLIED else WebhookOutcome.STALE_IGNORED

            self._uow.collect_events(record.pull_events())
            await self._inbox.mark_processed(event.event_id, now)
            await self._uow.commit()
            return outcome
