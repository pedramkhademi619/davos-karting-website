from davos.modules.identity.application.ports.otp_delivery import OtpDelivery
from davos.modules.identity.domain.value_objects.mobile_number import MobileNumber


class FakeOtpDelivery(OtpDelivery):
    def __init__(self, *, succeed: bool = True) -> None:
        self.succeed = succeed
        self.sent: list[tuple[str, str]] = []

    async def send(self, mobile: MobileNumber, code: str, ttl_seconds: int) -> bool:
        self.sent.append((mobile.e164, code))
        return self.succeed

    @property
    def last_code(self) -> str:
        return self.sent[-1][1]
