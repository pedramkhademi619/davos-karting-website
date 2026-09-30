from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.notifications.application.ports.sms_log_page import SmsLogPage
from davos.modules.notifications.domain.enums.sms_delivery_status import SmsDeliveryStatus
from davos.modules.notifications.domain.value_objects.sms_log_entry import SmsLogEntry


class SmsLogRepository(ABC):
    @abstractmethod
    async def add_many(self, entries: list[SmsLogEntry]) -> None: ...

    @abstractmethod
    async def page(self, *, text: str, offset: int, limit: int) -> SmsLogPage: ...

    @abstractmethod
    async def pending_message_ids(self, *, since: datetime, limit: int) -> list[str]: ...

    @abstractmethod
    async def update_statuses(self, statuses: dict[str, SmsDeliveryStatus], now: datetime) -> int: ...
