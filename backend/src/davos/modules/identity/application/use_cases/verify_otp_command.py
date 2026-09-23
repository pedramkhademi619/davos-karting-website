from dataclasses import dataclass


@dataclass(frozen=True)
class VerifyOtpCommand:
    raw_mobile: str
    code: str
    client_ip: str
    user_agent: str
