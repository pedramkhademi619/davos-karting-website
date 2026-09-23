from __future__ import annotations

import logging

from davos.modules.identity.application.ports.otp_delivery import OtpDelivery
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber
from davos.modules.notifications.application.ports.sms_gateway_port import SmsGatewayPort
from davos.modules.notifications.application.ports.sms_message import SmsMessage
from davos.modules.notifications.application.ports.sms_provider_error import SmsProviderError

logger = logging.getLogger(__name__)


class SmsOtpDelivery(OtpDelivery):
    """Bridges the identity module's OtpDelivery port onto the notifications SmsGatewayPort.

    Lives in the composition layer so the two modules never import each other.
    """

    TEMPLATE_KEY = "otp"

    def __init__(self, gateway: SmsGatewayPort) -> None:
        self._gateway = gateway

    async def send(self, mobile: MobileNumber, code: str, ttl_seconds: int) -> bool:
        message = SmsMessage(
            to_local_mobile=mobile.local,
            template_key=self.TEMPLATE_KEY,
            parameters={"code": code, "ttl_minutes": str(max(ttl_seconds // 60, 1))},
        )
        try:
            await self._gateway.send(message)
        except SmsProviderError:
            logger.warning("OTP SMS delivery failed for %s", mobile.masked())
            return False
        return True
