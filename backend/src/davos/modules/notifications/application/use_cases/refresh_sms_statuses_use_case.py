from __future__ import annotations

import logging
from datetime import timedelta

from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class RefreshSmsStatusesUseCase:
    """Asks the provider for the delivery status of recent messages that are not final yet."""

    def __init__(self, *, uow: UnitOfWork, gateway: SmsGatewayPort, log: SmsLogRepository, clock: Clock) -> None:
        self._uow = uow
        self._gateway = gateway
        self._log = log
        self._clock = clock

    async def execute(self, *, days: int = 3, batch: int = 500) -> int:
        now = self._clock.now()
        async with self._uow:
            ids = await self._log.pending_message_ids(since=now - timedelta(days=days), limit=batch)
        if not ids:
            return 0
        try:
            statuses = await self._gateway.delivery_statuses(ids)
        except SmsProviderError:
            logger.warning("sms delivery statuses unavailable; will try again")
            return 0
        async with self._uow:
            changed = await self._log.update_statuses(statuses, self._clock.now())
            await self._uow.commit()
        return changed
