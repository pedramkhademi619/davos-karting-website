from __future__ import annotations

import logging
import uuid

from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.enums.sms_kind import SmsKind
from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry
from davos.modules.notifications.domain.value_objects.sms_recipient import SmsRecipient
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class SendTransactionalSmsUseCase:
    """A message the customer expects (booking confirmation). ``summary`` is what the admin log shows.

    Raises SmsProviderError when the provider answered "try again later", so a queue can retry.
    """

    def __init__(self, *, uow: UnitOfWork, gateway: SmsGatewayPort, log: SmsLogRepository, clock: Clock) -> None:
        self._uow = uow
        self._gateway = gateway
        self._log = log
        self._clock = clock

    async def execute(self, message: SmsMessage, *, summary: str) -> bool:
        recipient = SmsRecipient.parse(message.to_local_mobile)
        message_id: str | None = None
        error = ""
        try:
            result = await self._gateway.send(message)
            message_id = result.provider_message_id
        except SmsProviderError as exc:
            if exc.retryable:
                raise
            error = str(exc)[:200]
            logger.warning("transactional sms to %s refused: %s", recipient.masked(), error)
        now = self._clock.now()
        async with self._uow:
            await self._log.add_many(
                [
                    SmsLogEntry(
                        entry_id=uuid.uuid4(),
                        kind=SmsKind.TRANSACTIONAL,
                        recipient=recipient.local,
                        body=summary[:600],
                        status=SmsDeliveryStatus.QUEUED if message_id else SmsDeliveryStatus.FAILED,
                        created_at=now,
                        updated_at=now,
                        provider_message_id=message_id,
                        sent_by="system",
                        error=error,
                    )
                ]
            )
            await self._uow.commit()
        return message_id is not None
