from __future__ import annotations

from davos.modules.accounting.application.ports.accounting_settings_repository import AccountingSettingsRepository
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork


class AccountingSettingsUseCase:
    def __init__(self, *, uow: UnitOfWork, settings: AccountingSettingsRepository, clock: Clock) -> None:
        self._uow = uow
        self._settings = settings
        self._clock = clock

    async def get(self) -> AccountingSettings:
        async with self._uow:
            return await self._settings.get()

    async def update(self, settings: AccountingSettings) -> AccountingSettings:
        async with self._uow:
            await self._settings.save(settings, self._clock.now())
            await self._uow.commit()
        return settings
