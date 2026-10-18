from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings


class AccountingSettingsRepository(ABC):
    @abstractmethod
    async def get(self) -> AccountingSettings: ...

    @abstractmethod
    async def save(self, settings: AccountingSettings, now: datetime) -> None: ...
