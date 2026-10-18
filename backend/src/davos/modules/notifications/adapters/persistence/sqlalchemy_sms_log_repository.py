from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, or_, select, text, update

from davos.modules.notifications.adapters.persistence.sms_message_model import SmsMessageModel
from davos.modules.notifications.application.ports.sms_log_page import SmsLogPage
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.enums.sms_kind import SmsKind
from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

M = SmsMessageModel


class SqlAlchemySmsLogRepository(SmsLogRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add_many(self, entries: list[SmsLogEntry]) -> None:
        self._uow.session.add_all(
            [
                M(
                    id=e.entry_id,
                    kind=e.kind.value,
                    recipient=e.recipient,
                    body=e.body,
                    status=e.status.value,
                    provider_message_id=e.provider_message_id,
                    batch_id=e.batch_id,
                    sent_by=e.sent_by,
                    error=e.error,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                )
                for e in entries
            ]
        )
        await self._uow.session.flush()

    async def page(self, *, text: str, offset: int, limit: int) -> SmsLogPage:
        where = text_filter(text)
        total = (await self._uow.session.execute(select(func.count()).select_from(M).where(where))).scalar_one()
        result = await self._uow.session.execute(
            select(M).where(where).order_by(M.created_at.desc()).offset(max(offset, 0)).limit(min(max(limit, 1), 200))
        )
        return SmsLogPage(items=[self._entry(m) for m in result.scalars()], total=int(total))

    async def pending_message_ids(self, *, since: datetime, limit: int) -> list[str]:
        result = await self._uow.session.execute(
            select(M.provider_message_id)
            .where(
                M.status.in_(("queued", "sent", "unknown")),
                M.created_at >= since,
                M.provider_message_id.is_not(None),
                ~M.provider_message_id.startswith("dev-"),
            )
            .order_by(M.created_at)
            .limit(limit)
        )
        return [str(v) for v in result.scalars() if v]

    async def update_statuses(self, statuses: dict[str, SmsDeliveryStatus], now: datetime) -> int:
        changed = 0
        for message_id, status in statuses.items():
            result = await self._uow.session.execute(
                update(M)
                .where(M.provider_message_id == message_id, M.status != status.value)
                .values(status=status.value, updated_at=now)
            )
            changed += int(result.rowcount or 0)  # type: ignore[attr-defined]
        return changed

    @staticmethod
    def _entry(model: SmsMessageModel) -> SmsLogEntry:
        return SmsLogEntry(
            entry_id=model.id,
            kind=SmsKind(model.kind),
            recipient=model.recipient,
            body=model.body,
            status=SmsDeliveryStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            provider_message_id=model.provider_message_id,
            batch_id=model.batch_id,
            sent_by=model.sent_by,
            error=model.error,
        )


def text_filter(needle: str):  # type: ignore[no-untyped-def]
    needle = needle.strip()
    if not needle:
        return text("true")
    pattern = "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    return or_(M.recipient.ilike(pattern, escape="\\"), M.body.ilike(pattern, escape="\\"))
