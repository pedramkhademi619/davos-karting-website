from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select

from davos.modules.reservations.adapters.persistence.reservation_model import ReservationModel
from davos.modules.reservations.application.ports.reservation_stats import ReservationStats
from davos.modules.reservations.application.ports.reservation_stats_reader import ReservationStatsReader
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

R = ReservationModel


class SqlAlchemyReservationStatsReader(ReservationStatsReader):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def stats(self, date_from: date, date_to: date) -> ReservationStats:
        taking = R.status.in_(("confirmed", "attended"))

        def count(status: str):  # type: ignore[no-untyped-def]
            return func.coalesce(func.sum(case((R.status == status, 1), else_=0)), 0)

        result = await self._uow.session.execute(
            select(
                count("confirmed"),
                count("attended"),
                count("cancelled"),
                count("held"),
                func.coalesce(func.sum(case((taking, R.single_count + R.double_count), else_=0)), 0),
                func.coalesce(func.sum(case((taking, R.single_count + 2 * R.double_count), else_=0)), 0),
                func.coalesce(func.sum(case((taking & (R.source == "online"), R.amount_irr), else_=0)), 0),
            ).where(R.business_date >= date_from, R.business_date <= date_to)
        )
        row = result.one()
        return ReservationStats(*(int(v) for v in row))
