from __future__ import annotations

from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo
from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_log_page import SmsLogPage
from davos.modules.notifications.application.ports.sms_log_repository import SmsLogRepository
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class SmsPanelUseCase:
    """Read side of the admin SMS panel: the sent-messages log and the provider account."""

    def __init__(self, *, uow: UnitOfWork, gateway: SmsGatewayPort, log: SmsLogRepository) -> None:
        self._uow = uow
        self._gateway = gateway
        self._log = log

    async def history(self, *, text: str = "", offset: int = 0, limit: int = 50) -> SmsLogPage:
        async with self._uow:
            return await self._log.page(text=text, offset=offset, limit=limit)

    async def account(self) -> SmsAccountInfo | None:
        try:
            return await self._gateway.account()
        except SmsProviderError:
            return None
