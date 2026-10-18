from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from davos.modules.reservations.adapters.persistence.schedule_settings_codec import ScheduleSettingsCodec
from davos.modules.reservations.adapters.persistence.schedule_settings_model import ScheduleSettingsModel
from davos.modules.reservations.application.ports.schedule_settings_repository import ScheduleSettingsRepository
from davos.modules.reservations.domain.value_objects.schedule_settings import ScheduleSettings
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyScheduleSettingsRepository(ScheduleSettingsRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def get(self) -> ScheduleSettings:
        result = await self._uow.session.execute(
            select(ScheduleSettingsModel.data).where(ScheduleSettingsModel.id == 1)
        )
        data = result.scalar_one_or_none()
        return ScheduleSettingsCodec.decode(data) if data else ScheduleSettings()

    async def save(self, settings: ScheduleSettings, now: datetime) -> None:
        data = ScheduleSettingsCodec.encode(settings)
        statement = insert(ScheduleSettingsModel).values(id=1, data=data, updated_at=now)
        await self._uow.session.execute(
            statement.on_conflict_do_update(index_elements=["id"], set_={"data": data, "updated_at": now})
        )
