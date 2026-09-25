from enum import StrEnum


class PaymentStatus(StrEnum):
    CREATED = "created"
    REDIRECTED = "redirected"
    VERIFYING = "verifying"
    UNKNOWN = "unknown"  # verification could not be completed (timeout / outage): reconcile, never assume
    PAID = "paid"  # verified by the bank and accepted for the order; ``settled_at`` tells whether funds were settled
    FAILED = "failed"
    EXPIRED = "expired"
    REFUND_PENDING = "refund_pending"  # the bank took the money but the order cannot accept it: must be reversed
    REVERSED = "reversed"  # the money went back to the customer

    @property
    def is_terminal(self) -> bool:
        return self in {PaymentStatus.FAILED, PaymentStatus.EXPIRED, PaymentStatus.REVERSED}
