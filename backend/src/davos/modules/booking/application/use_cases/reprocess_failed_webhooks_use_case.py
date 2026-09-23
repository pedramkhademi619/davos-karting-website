from __future__ import annotations

import logging

from davos.modules.booking.application.ports.webhook_inbox_repository import WebhookInboxRepository
from davos.modules.booking.application.services.booking_event_processor import BookingEventProcessor
from davos.modules.booking.domain.services.booking_event_parser import BookingEventParser
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ReprocessFailedWebhooksUseCase:
    """Operator-triggered retry of events that failed earlier (bodies were signature-checked on receipt)."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        inbox: WebhookInboxRepository,
        parser: BookingEventParser,
        processor: BookingEventProcessor,
    ) -> None:
        self._uow = uow
        self._inbox = inbox
        self._parser = parser
        self._processor = processor

    async def execute(self, limit: int = 50) -> tuple[int, int]:
        """Returns (recovered, still_failing)."""
        async with self._uow:
            failed = await self._inbox.list_failed(limit)
        recovered = still_failing = 0
        for item in failed:
            try:
                await self._processor.process(self._parser.parse(item.body.encode("utf-8")), item.body)
                recovered += 1
            except Exception:
                logger.warning("reprocessing of booking event %s failed again", item.event_id)
                still_failing += 1
        return recovered, still_failing
