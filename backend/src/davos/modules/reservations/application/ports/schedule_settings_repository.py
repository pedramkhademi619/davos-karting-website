from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings


class ScheduleSettingsRepository(ABC):
    @abstractmethod
    async def get(self) -> ScheduleSettings:
        """The stored settings, or the defaults when the owner has never saved any."""

    @abstractmethod
    async def save(self, settings: ScheduleSettings, now: datetime) -> None: ...
