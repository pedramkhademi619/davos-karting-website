import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class StartPaymentResult:
    payment_id: uuid.UUID
    redirect_url: str
    method: str = "GET"
    form_fields: dict[str, str] = field(default_factory=dict)
