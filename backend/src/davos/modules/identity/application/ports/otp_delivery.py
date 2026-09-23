from abc import ABC, abstractmethod

from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


class OtpDelivery(ABC):
    """Outbound port owned by the identity module; composition maps it onto the SMS gateway."""

    @abstractmethod
    async def send(self, mobile: MobileNumber, code: str, ttl_seconds: int) -> bool:
        """Return True when the provider accepted the message."""
