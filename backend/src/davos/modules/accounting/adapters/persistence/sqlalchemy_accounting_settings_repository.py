from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from davos.modules.accounting.adapters.persistence.accounting_settings_codec import AccountingSettingsCodec
from davos.modules.accounting.adapters.persistence.accounting_settings_model import AccountingSettingsModel
from davos.modules.accounting.application.ports.accounting_settings_repository import AccountingSettingsRepository
from davos.modules.accounting.domain.value_objects.accounting_settings import AccountingSettings
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyAccountingSettingsRepository(AccountingSettingsRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get(self) -> AccountingSettings:
        result = await self._uow.session.execute(
            select(AccountingSettingsModel.data).where(AccountingSettingsModel.id == 1)
        )
        data = result.scalar_one_or_none()
        return AccountingSettingsCodec.decode(data) if data else AccountingSettings()

    async def save(self, settings: AccountingSettings, now: datetime) -> None:
        data = AccountingSettingsCodec.encode(settings)
        statement = insert(AccountingSettingsModel).values(id=1, data=data, updated_at=now)
        await self._uow.session.execute(
            statement.on_conflict_do_update(index_elements=["id"], set_={"data": data, "updated_at": now})
        )
