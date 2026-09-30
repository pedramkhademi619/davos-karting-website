from __future__ import annotations

import logging
import uuid

from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.modules.notifications.application.use_cases.bulk_sms_report import BulkSmsReport
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.enums.sms_kind import SmsKind
from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry
from davos.modules.notifications.domain.value_objects.sms_recipient import SmsRecipient
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError

logger = logging.getLogger(__name__)

MAX_RECIPIENTS = 5000
MAX_TEXT_CHARS = 600
_CHUNK = 100


class SendBulkSmsUseCase:
    """Staff send one text to many customers. Every recipient gets a log line with its delivery status."""

    def __init__(self, *, uow: UnitOfWork, gateway: SmsGatewayPort, log: SmsLogRepository, clock: Clock) -> None:
        self._uow = uow
        self._gateway = gateway
        self._log = log
        self._clock = clock

    async def execute(self, *, recipients: list[str], text: str, sent_by: str) -> BulkSmsReport:
        text = text.strip()
        if not text:
            raise ValidationError("متن پیامک خالی است.", code="sms_text_empty")
        if len(text) > MAX_TEXT_CHARS:
            raise ValidationError(f"متن پیامک حداکثر {MAX_TEXT_CHARS} نویسه است.", code="sms_text_too_long")

        valid: list[str] = []
        invalid: list[str] = []
        for raw in recipients:
            try:
                number = SmsRecipient.parse(raw).local
            except ValidationError:
                invalid.append(raw[:20])
                continue
            if number not in valid:
                valid.append(number)
        if not valid:
            raise ValidationError("هیچ شماره معتبری انتخاب نشده است.", code="sms_no_recipients")
        if len(valid) > MAX_RECIPIENTS:
            raise ValidationError(f"حداکثر {MAX_RECIPIENTS} گیرنده در هر ارسال.", code="sms_too_many_recipients")

        batch_id = uuid.uuid4()
        accepted = failed = 0
        for start in range(0, len(valid), _CHUNK):
            chunk = valid[start : start + _CHUNK]
            try:
                results = await self._gateway.send_text(chunk, text)
            except SmsProviderError as exc:
                logger.warning("bulk sms chunk refused by the provider")
                entries = [
                    self._entry(n, text, batch_id, sent_by, None, SmsDeliveryStatus.FAILED, str(exc)) for n in chunk
                ]
                failed += len(chunk)
            else:
                by_number = {r.recipient: r.provider_message_id for r in results}
                entries = []
                for number in chunk:
                    message_id = by_number.get(number)
                    status = SmsDeliveryStatus.QUEUED if message_id else SmsDeliveryStatus.FAILED
                    entries.append(self._entry(number, text, batch_id, sent_by, message_id, status, ""))
                    accepted += message_id is not None
                    failed += message_id is None
            async with self._uow:
                await self._log.add_many(entries)
                await self._uow.commit()
        return BulkSmsReport(batch_id=batch_id, accepted=accepted, failed=failed, invalid_numbers=invalid)

    def _entry(
        self,
        number: str,
        text: str,
        batch_id: uuid.UUID,
        sent_by: str,
        message_id: str | None,
        status: SmsDeliveryStatus,
        error: str,
    ) -> SmsLogEntry:
        now = self._clock.now()
        return SmsLogEntry(
            entry_id=uuid.uuid4(),
            kind=SmsKind.BULK,
            recipient=number,
            body=text,
            status=status,
            created_at=now,
            updated_at=now,
            provider_message_id=message_id,
            batch_id=batch_id,
            sent_by=sent_by[:60],
            error=error[:200],
        )
