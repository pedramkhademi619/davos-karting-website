from __future__ import annotations

from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class ScheduleSettingsUseCase:
    """Read and replace the owner's booking settings (validated by ScheduleSettings itself)."""

    def __init__(self, *, uow: UnitOfWork, settings: ScheduleSettingsRepository, clock: Clock) -> None:
        self._uow = uow
        self._settings = settings
        self._clock = clock

    async def get(self) -> ScheduleSettings:
        async with self._uow:
            return await self._settings.get()

    async def replace(self, settings: ScheduleSettings) -> ScheduleSettings:
        async with self._uow:
            await self._settings.save(settings, self._clock.now())
            await self._uow.commit()
        return settings
