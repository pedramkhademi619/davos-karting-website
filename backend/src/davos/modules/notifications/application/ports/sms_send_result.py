from dataclasses import dataclass


@dataclass(frozen=True)
class SmsSendResult:
    provider_message_id: str
