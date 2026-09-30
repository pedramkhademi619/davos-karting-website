from enum import StrEnum


class SmsDeliveryStatus(StrEnum):
    QUEUED = "queued"  # accepted by the provider, not yet handed to the operator
    SENT = "sent"  # handed to the mobile operator
    DELIVERED = "delivered"
    FAILED = "failed"
    BLOCKED = "blocked"  # the recipient blocked promotional messages
    UNKNOWN = "unknown"

    @property
    def is_final(self) -> bool:
        return self in {SmsDeliveryStatus.DELIVERED, SmsDeliveryStatus.FAILED, SmsDeliveryStatus.BLOCKED}
