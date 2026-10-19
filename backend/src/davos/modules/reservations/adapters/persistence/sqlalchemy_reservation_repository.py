from __future__ import annotations

import uuid
from datetime import date, datetime, time

from sqlalchemy import String, and_, cast, func, or_, select, text, update
from sqlalchemy.dialects.postgresql import insert

from davos.modules.reservations.adapters.persistence.reservation_mapper import ReservationMapper
from davos.modules.reservations.adapters.persistence.reservation_model import ReservationModel
from davos.modules.reservations.adapters.persistence.reservation_ticket_counter_model import (
    ReservationTicketCounterModel,
)
from davos.modules.reservations.application.ports.reservation_page import ReservationPage
from davos.modules.reservations.application.ports.reservation_query import ReservationQuery
from davos.modules.reservations.application.ports.reservation_repository import ReservationRepository
from davos.modules.reservations.domain.entities.reservation import Reservation
from davos.modules.reservations.domain.value_objects.daily_online_load import DailyOnlineLoad
from davos.modules.reservations.domain.value_objects.session_load import SessionLoad
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

R = ReservationModel


def _occupying(now: datetime):  # type: ignore[no-untyped-def]
    """Rows that take karts: confirmed or attended, or a hold that has not run out yet."""
    return or_(R.status.in_(("confirmed", "attended")), and_(R.status == "held", R.hold_expires_at > now))


FIRST_TICKET_NUMBER = 100  # every shift's first ticket


class SqlAlchemyReservationRepository(ReservationRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def next_ticket_number(self, shift_key: str) -> int:
        """100 for the first ticket of a shift, then 101, 102... The upsert is one atomic statement per ticket."""
        statement = (
            insert(ReservationTicketCounterModel)
            .values(shift_key=shift_key, last_value=FIRST_TICKET_NUMBER)
            .on_conflict_do_update(
                index_elements=[ReservationTicketCounterModel.shift_key],
                set_={"last_value": ReservationTicketCounterModel.last_value + 1},
            )
            .returning(ReservationTicketCounterModel.last_value)
        )
        return int((await self._uow.session.execute(statement)).scalar_one())

    async def add(self, reservation: Reservation) -> None:
        self._uow.session.add(ReservationMapper.to_model(reservation))
        await self._uow.session.flush()

    async def save(self, reservation: Reservation) -> None:
        await self._uow.session.execute(
            update(R).where(R.id == reservation.id).values(**ReservationMapper.mutable_values(reservation))
        )

    async def get_for_update(self, reservation_id: uuid.UUID) -> Reservation | None:
        result = await self._uow.session.execute(select(R).where(R.id == reservation_id).with_for_update())
        model = result.scalar_one_or_none()
        return ReservationMapper.to_domain(model) if model else None

    async def get(self, reservation_id: uuid.UUID) -> Reservation | None:
        result = await self._uow.session.execute(select(R).where(R.id == reservation_id))
        model = result.scalar_one_or_none()
        return ReservationMapper.to_domain(model) if model else None

    async def lock_session(self, day: date, session_time: time) -> None:
        # A transaction-scoped advisory lock per session: released automatically at commit or rollback.
        key = f"reservation-session:{day.isoformat()}:{session_time.strftime('%H:%M')}"
        await self._uow.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})

    async def session_load(self, day: date, session_time: time, now: datetime) -> SessionLoad:
        result = await self._uow.session.execute(
            select(func.coalesce(func.sum(R.single_count), 0), func.coalesce(func.sum(R.double_count), 0)).where(
                R.business_date == day, R.session_time == session_time, _occupying(now)
            )
        )
        singles, doubles = result.one()
        return SessionLoad(int(singles), int(doubles))

    async def day_loads(self, day: date, now: datetime) -> dict[time, SessionLoad]:
        result = await self._uow.session.execute(
            select(R.session_time, func.sum(R.single_count), func.sum(R.double_count))
            .where(R.business_date == day, _occupying(now))
            .group_by(R.session_time)
        )
        return {row[0]: SessionLoad(int(row[1]), int(row[2])) for row in result}

    async def lock_day(self, day: date) -> None:
        # A transaction-scoped advisory lock per business day: released automatically at commit or rollback. Always
        # taken before lock_session (consistent ordering, so the two can never deadlock against each other).
        key = f"reservation-day:{day.isoformat()}"
        await self._uow.session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key})

    async def day_online_load(self, day: date, now: datetime) -> DailyOnlineLoad:
        result = await self._uow.session.execute(
            select(func.count(), func.coalesce(func.sum(R.single_count + 2 * R.double_count), 0)).where(
                R.business_date == day, R.source == "online", _occupying(now)
            )
        )
        tickets, people = result.one()
        return DailyOnlineLoad(int(tickets), int(people))

    async def count_active_holds(self, customer_id: uuid.UUID, now: datetime) -> int:
        result = await self._uow.session.execute(
            select(func.count()).where(R.customer_id == customer_id, R.status == "held", R.hold_expires_at > now)
        )
        return int(result.scalar_one())

    async def list_for_customer(self, customer_id: uuid.UUID, *, limit: int) -> list[Reservation]:
        result = await self._uow.session.execute(
            select(R)
            .where(R.customer_id == customer_id, R.status != "expired")
            .order_by(R.starts_at.desc())
            .limit(limit)
        )
        return [ReservationMapper.to_domain(m) for m in result.scalars()]

    async def search(self, query: ReservationQuery) -> ReservationPage:
        conditions = []
        if query.date_from is not None:
            conditions.append(R.business_date >= query.date_from)
        if query.date_to is not None:
            conditions.append(R.business_date <= query.date_to)
        if query.status is not None:
            conditions.append(R.status == query.status.value)
        if query.source is not None:
            conditions.append(R.source == query.source.value)
        needle = query.text.strip()
        if needle:
            pattern = "%" + needle.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
            conditions.append(
                or_(
                    R.code.ilike(pattern, escape="\\"),
                    cast(R.ticket_number, String).ilike(pattern, escape="\\"),
                    R.contact_name.ilike(pattern, escape="\\"),
                    R.contact_mobile.ilike(pattern, escape="\\"),
                )
            )
        where = and_(*conditions) if conditions else text("true")
        total = (await self._uow.session.execute(select(func.count()).select_from(R).where(where))).scalar_one()
        result = await self._uow.session.execute(
            select(R)
            .where(where)
            .order_by(R.business_date.desc(), R.starts_at.asc(), R.created_at.asc())
            .offset(max(query.offset, 0))
            .limit(min(max(query.limit, 1), 200))
        )
        return ReservationPage(items=[ReservationMapper.to_domain(m) for m in result.scalars()], total=int(total))

    async def list_overdue_holds(self, now: datetime, *, limit: int) -> list[uuid.UUID]:
        result = await self._uow.session.execute(
            select(R.id).where(R.status == "held", R.hold_expires_at <= now).order_by(R.hold_expires_at).limit(limit)
        )
        return list(result.scalars())
