from dataclasses import dataclass, field


@dataclass(frozen=True)
class PaymentSession:
    """Where to send the browser. Some gateways (Mellat) must be opened with a POST form, others with a plain link."""

    authority: str
    redirect_url: str
    method: str = "GET"
    form_fields: dict[str, str] = field(default_factory=dict)
