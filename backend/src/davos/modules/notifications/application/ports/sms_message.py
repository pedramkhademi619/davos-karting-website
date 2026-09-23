from dataclasses import dataclass, field


@dataclass(frozen=True)
class SmsMessage:
    """Provider-agnostic template message. Marketing messages must carry consent upstream."""

    to_local_mobile: str
    template_key: str
    parameters: dict[str, str] = field(default_factory=dict)
    idempotency_key: str | None = None
