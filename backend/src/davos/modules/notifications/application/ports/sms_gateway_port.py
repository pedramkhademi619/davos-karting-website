from abc import ABC, abstractmethod

from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult


class SmsGatewayPort(ABC):
    @abstractmethod
    async def send(self, message: SmsMessage) -> SmsSendResult:
        """Send one template message. Raises ``SmsProviderError`` on failure."""
