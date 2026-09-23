from dataclasses import dataclass


@dataclass(frozen=True)
class RequestOtpCommand:
    raw_mobile: str
    client_ip: str
