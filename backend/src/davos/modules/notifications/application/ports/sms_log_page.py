from __future__ import annotations

from dataclasses import dataclass

from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry


@dataclass(frozen=True)
class SmsLogPage:
    items: list[SmsLogEntry]
    total: int
