from __future__ import annotations

import logging
import uuid

from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult

logger = logging.getLogger(__name__)


class RecordingSmsGateway(SmsGatewayPort):
    """Development adapter: nothing is sent to a real network.

    Limitations (by design): messages live in process memory only, and delivery status
    callbacks are not simulated. When ``echo`` is enabled (explicit development switch) the
    parameters, including OTP codes, are logged; otherwise only the template key is logged.
    """

    def __init__(self, *, echo: bool = False) -> None:
        self._echo = echo
        self.sent: list[SmsMessage] = []

    async def send(self, message: SmsMessage) -> SmsSendResult:
        self.sent.append(message)
        if self._echo:
            logger.warning(
                "DEV SMS to=%s template=%s params=%s", message.to_local_mobile, message.template_key, message.parameters
            )
        else:
            logger.info("SMS accepted by recording gateway template=%s", message.template_key)
        return SmsSendResult(provider_message_id=f"dev-{uuid.uuid4()}")
