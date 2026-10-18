from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry


class SmsLogResponse(BaseModel):
    id: uuid.UUID
    kind: str
    recipient: str
    body: str
    status: str
    created_at: datetime
    updated_at: datetime
    sent_by: str
    error: str

    @classmethod
    def of(cls, e: SmsLogEntry) -> SmsLogResponse:
        return cls(
            id=e.entry_id,
            kind=e.kind.value,
            recipient=e.recipient,
            body=e.body,
            status=e.status.value,
            created_at=e.created_at,
            updated_at=e.updated_at,
            sent_by=e.sent_by,
            error=e.error,
        )
