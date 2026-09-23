from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSession:
    authority: str
    redirect_url: str
