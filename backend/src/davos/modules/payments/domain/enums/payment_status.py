from enum import StrEnum


class PaymentStatus(StrEnum):
    CREATED = "created"
    REDIRECTED = "redirected"
    VERIFYING = "verifying"
    UNKNOWN = "unknown"  # verification could not be completed (timeout / outage): reconcile, never assume
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"

    @property
    def is_terminal(self) -> bool:
        return self in {PaymentStatus.PAID, PaymentStatus.FAILED, PaymentStatus.EXPIRED}
