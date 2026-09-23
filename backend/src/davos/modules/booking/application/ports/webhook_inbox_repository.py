from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.booking.application.ports.failed_webhook import FailedWebhook
from davos.modules.booking.application.ports.inbox_status import InboxStatus


class WebhookInboxRepository(ABC):
    @abstractmethod
    async def register(self, event_id: str, body: str, now: datetime) -> InboxStatus | None:
        """Record receipt. Returns None for a first delivery, or the stored status for a repeat."""

    @abstractmethod
    async def mark_processed(self, event_id: str, now: datetime) -> None: ...

    @abstractmethod
    async def mark_failed(self, event_id: str, body: str, error_code: str, now: datetime) -> None:
        """Upsert the event as FAILED and count the attempt, so it can be reprocessed later."""

    @abstractmethod
    async def list_failed(self, limit: int) -> list[FailedWebhook]: ...
