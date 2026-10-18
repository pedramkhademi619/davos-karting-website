from abc import ABC, abstractmethod

from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus


class SmsGatewayPort(ABC):
    @abstractmethod
    async def send(self, message: SmsMessage) -> SmsSendResult:
        """Send one template message. Raises ``SmsProviderError`` on failure."""

    @abstractmethod
    async def send_text(self, recipients: list[str], text: str) -> list[SmsSendResult]:
        """Send one free text to up to 100 local numbers. Raises ``SmsProviderError`` on failure."""

    @abstractmethod
    async def delivery_statuses(self, message_ids: list[str]) -> dict[str, SmsDeliveryStatus]:
        """Current delivery status of up to 500 messages. Raises ``SmsProviderError`` on failure."""

    @abstractmethod
    async def account(self) -> SmsAccountInfo | None:
        """Remaining credit, or None when the provider has no account (development)."""
