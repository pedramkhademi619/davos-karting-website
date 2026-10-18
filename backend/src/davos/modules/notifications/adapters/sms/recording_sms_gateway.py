from __future__ import annotations

import logging
import uuid

from davos.modules.notifications.adapters.sms.sms_text_templates import render
from davos.modules.notifications.application.ports.sms_account_info import SmsAccountInfo
from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_send_result import SmsSendResult
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus

logger = logging.getLogger(__name__)


class RecordingSmsGateway(SmsGatewayPort):
    """Development adapter: nothing is sent to a real network.

    Messages live in process memory only and every message counts as delivered. When ``echo`` is enabled (explicit
    development switch) the text, including one-time codes, is logged; otherwise only the template key is logged.
    """

    def __init__(self, *, echo: bool = False) -> None:
        self._echo = echo
        self.sent: list[SmsMessage] = []
        self.texts: list[tuple[list[str], str]] = []

    async def send(self, message: SmsMessage) -> SmsSendResult:
        self.sent.append(message)
        if self._echo:
            logger.warning(
                "DEV SMS to=%s text=%s", message.to_local_mobile, render(message.template_key, message.parameters)
            )
        else:
            logger.info("SMS accepted by recording gateway template=%s", message.template_key)
        return SmsSendResult(provider_message_id=f"dev-{uuid.uuid4()}", recipient=message.to_local_mobile)

    async def send_text(self, recipients: list[str], text: str) -> list[SmsSendResult]:
        self.texts.append((list(recipients), text))
        if self._echo:
            logger.warning("DEV SMS to %d recipients text=%s", len(recipients), text)
        return [SmsSendResult(provider_message_id=f"dev-{uuid.uuid4()}", recipient=r) for r in recipients]

    async def delivery_statuses(self, message_ids: list[str]) -> dict[str, SmsDeliveryStatus]:
        return dict.fromkeys(message_ids, SmsDeliveryStatus.DELIVERED)

    async def account(self) -> SmsAccountInfo | None:
        return None
