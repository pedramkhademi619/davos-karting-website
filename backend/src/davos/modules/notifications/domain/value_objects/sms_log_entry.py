from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.enums.sms_kind import SmsKind


@dataclass(frozen=True)
class SmsLogEntry:
    """One message to one recipient, as shown in the admin panel. One-time codes are never logged."""

    entry_id: uuid.UUID
    kind: SmsKind
    recipient: str
    body: str
    status: SmsDeliveryStatus
    created_at: datetime
    updated_at: datetime
    provider_message_id: str | None = None
    batch_id: uuid.UUID | None = None
    sent_by: str = ""
    error: str = ""
