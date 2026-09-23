from dataclasses import dataclass


@dataclass(frozen=True)
class FailedWebhook:
    event_id: str
    body: str
    attempts: int
    last_error_code: str | None
