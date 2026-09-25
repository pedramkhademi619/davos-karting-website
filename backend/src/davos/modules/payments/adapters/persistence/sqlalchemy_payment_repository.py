from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, func, or_, select, text, update

from davos.modules.payments.adapters.persistence.payment_attempt_mapper import PaymentAttemptMapper
from davos.modules.payments.adapters.persistence.payment_attempt_model import (
    GATEWAY_ORDER_SEQUENCE,
    PaymentAttemptModel,
)
from davos.modules.payments.application.ports.payment_page import PaymentPage
from davos.modules.payments.application.ports.payment_query import PaymentQuery
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork

P = PaymentAttemptModel


class SqlAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, payment: PaymentAttempt) -> None:
        self._uow.session.add(PaymentAttemptMapper.to_model(payment))
        await self._uow.session.flush()

    async def next_gateway_order_id(self) -> int:
        result = await self._uow.session.execute(select(GATEWAY_ORDER_SEQUENCE.next_value()))
        return int(result.scalar_one())

    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None:
        result = await self._uow.session.execute(select(P).where(P.id == payment_id).with_for_update())
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None:
        result = await self._uow.session.execute(select(P).where(P.authority == authority).with_for_update())
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None:
        result = await self._uow.session.execute(select(P).where(P.id == payment_id, P.customer_id == customer_id))
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def lock_order(self, order_ref: str) -> None:
        await self._uow.session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": f"payment-order:{order_ref}"}
        )

    async def has_paid_for_order(self, order_ref: str, *, excluding: uuid.UUID | None = None) -> bool:
        statement = select(P.id).where(P.order_ref == order_ref, P.status == "paid")
        if excluding is not None:
            statement = statement.where(P.id != excluding)
        result = await self._uow.session.execute(statement.limit(1))
        return result.first() is not None

    async def save(self, payment: PaymentAttempt) -> None:
        await self._uow.session.execute(
            update(P).where(P.id == payment.id).values(**PaymentAttemptMapper.mutable_values(payment))
        )

    async def search(self, query: PaymentQuery) -> PaymentPage:
        conditions = []
        if query.status is not None:
            conditions.append(P.status == query.status.value)
        if query.created_from is not None:
            conditions.append(P.created_at >= query.created_from)
        if query.created_to is not None:
            conditions.append(P.created_at < query.created_to)
        needle = query.text.strip()
        if needle:
            conditions.append(
                or_(
                    P.order_ref == needle,
                    P.reference_id == needle,
                    P.provider_reference == needle,
                    P.authority == needle,
                )
            )
        where = and_(*conditions) if conditions else text("true")
        totals = await self._uow.session.execute(
            select(func.count(), func.coalesce(func.sum(P.amount_irr).filter(P.status == "paid"), 0))
            .select_from(P)
            .where(where)
        )
        total, paid_total = totals.one()
        result = await self._uow.session.execute(
            select(P)
            .where(where)
            .order_by(P.created_at.desc())
            .offset(max(query.offset, 0))
            .limit(min(max(query.limit, 1), 200))
        )
        return PaymentPage(
            items=[PaymentAttemptMapper.to_domain(m) for m in result.scalars()],
            total=int(total),
            paid_total_irr=int(paid_total),
        )

    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        stuck_before = now - timedelta(seconds=stuck_for_seconds)
        result = await self._uow.session.execute(
            select(P.id)
            .where(
                or_(
                    and_(P.status.in_(("unknown", "verifying")), P.updated_at <= stuck_before),
                    and_(P.status == "paid", P.settled_at.is_(None), P.updated_at <= stuck_before),
                    P.status == "refund_pending",
                    and_(P.status.in_(("created", "redirected")), P.expires_at <= now),
                )
            )
            .order_by(P.updated_at)
            .limit(limit)
        )
        return list(result.scalars())
