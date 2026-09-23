from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from davos.modules.booking.adapters.persistence.booking_webhook_inbox_model import BookingWebhookInboxModel
from davos.modules.booking.application.ports.failed_webhook import FailedWebhook
from davos.modules.booking.application.ports.inbox_status import InboxStatus
from davos.modules.booking.application.ports.webhook_inbox_repository import WebhookInboxRepository
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyWebhookInboxRepository(WebhookInboxRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def register(self, event_id: str, body: str, now: datetime) -> InboxStatus | None:
        session = self._uow.session
        inserted = (
            await session.execute(
                insert(BookingWebhookInboxModel)
                .values(event_id=event_id, body=body, status=InboxStatus.RECEIVED.value, attempts=0, received_at=now)
                .on_conflict_do_nothing(index_elements=[BookingWebhookInboxModel.event_id])
                .returning(BookingWebhookInboxModel.event_id)
            )
        ).scalar_one_or_none()
        if inserted is not None:
            return None
        # A repeat delivery: lock the row so two concurrent copies of one event are processed one at a time.
        status = (
            await session.execute(
                select(BookingWebhookInboxModel.status)
                .where(BookingWebhookInboxModel.event_id == event_id)
                .with_for_update()
            )
        ).scalar_one()
        return InboxStatus(status)

    async def mark_processed(self, event_id: str, now: datetime) -> None:
        await self._uow.session.execute(
            update(BookingWebhookInboxModel)
            .where(BookingWebhookInboxModel.event_id == event_id)
            .values(status=InboxStatus.PROCESSED.value, processed_at=now, last_error_code=None)
        )

    async def mark_failed(self, event_id: str, body: str, error_code: str, now: datetime) -> None:
        statement = insert(BookingWebhookInboxModel).values(
            event_id=event_id,
            body=body,
            status=InboxStatus.FAILED.value,
            attempts=1,
            last_error_code=error_code,
            received_at=now,
        )
        await self._uow.session.execute(
            statement.on_conflict_do_update(
                index_elements=[BookingWebhookInboxModel.event_id],
                set_={
                    "status": InboxStatus.FAILED.value,
                    "last_error_code": error_code,
                    "attempts": BookingWebhookInboxModel.attempts + 1,
                },
                where=BookingWebhookInboxModel.status != InboxStatus.PROCESSED.value,
            )
        )

    async def list_failed(self, limit: int) -> list[FailedWebhook]:
        result = await self._uow.session.execute(
            select(BookingWebhookInboxModel)
            .where(BookingWebhookInboxModel.status == InboxStatus.FAILED.value)
            .order_by(BookingWebhookInboxModel.received_at)
            .limit(limit)
        )
        return [FailedWebhook(m.event_id, m.body, m.attempts, m.last_error_code) for m in result.scalars()]
