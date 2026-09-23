from __future__ import annotations

from datetime import datetime

from davos.modules.booking.application.ports.failed_webhook import FailedWebhook
from davos.modules.booking.application.ports.inbox_status import InboxStatus
from davos.modules.booking.application.ports.webhook_inbox_repository import WebhookInboxRepository


class InMemoryWebhookInbox(WebhookInboxRepository):
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, object]] = {}

    async def register(self, event_id: str, body: str, now: datetime) -> InboxStatus | None:
        if event_id in self.rows:
            return InboxStatus(str(self.rows[event_id]["status"]))
        self.rows[event_id] = {"body": body, "status": InboxStatus.RECEIVED.value, "attempts": 0, "error": None}
        return None

    async def mark_processed(self, event_id: str, now: datetime) -> None:
        self.rows[event_id]["status"] = InboxStatus.PROCESSED.value

    async def mark_failed(self, event_id: str, body: str, error_code: str, now: datetime) -> None:
        row = self.rows.setdefault(event_id, {"body": body, "attempts": 0})
        row.update(status=InboxStatus.FAILED.value, error=error_code, attempts=int(row["attempts"]) + 1)  # type: ignore[call-overload]

    async def list_failed(self, limit: int) -> list[FailedWebhook]:
        return [
            FailedWebhook(k, str(v["body"]), int(v["attempts"]), str(v["error"]))  # type: ignore[call-overload]
            for k, v in self.rows.items()
            if v["status"] == InboxStatus.FAILED.value
        ][:limit]
