from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select, update

from davos.modules.payments.adapters.persistence.payment_attempt_mapper import PaymentAttemptMapper
from davos.modules.payments.adapters.persistence.payment_attempt_model import PaymentAttemptModel
from davos.modules.payments.application.ports.payment_repository import PaymentRepository
from davos.modules.payments.domain.entities.payment_attempt import PaymentAttempt
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyPaymentRepository(PaymentRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, payment: PaymentAttempt) -> None:
        self._uow.session.add(PaymentAttemptMapper.to_model(payment))
        await self._uow.session.flush()

    async def get_for_update(self, payment_id: uuid.UUID) -> PaymentAttempt | None:
        result = await self._uow.session.execute(
            select(PaymentAttemptModel).where(PaymentAttemptModel.id == payment_id).with_for_update()
        )
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def get_by_authority_for_update(self, authority: str) -> PaymentAttempt | None:
        result = await self._uow.session.execute(
            select(PaymentAttemptModel).where(PaymentAttemptModel.authority == authority).with_for_update()
        )
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def get_owned(self, payment_id: uuid.UUID, customer_id: uuid.UUID) -> PaymentAttempt | None:
        result = await self._uow.session.execute(
            select(PaymentAttemptModel).where(
                PaymentAttemptModel.id == payment_id, PaymentAttemptModel.customer_id == customer_id
            )
        )
        model = result.scalar_one_or_none()
        return PaymentAttemptMapper.to_domain(model) if model else None

    async def has_paid_for_order(self, order_ref: str) -> bool:
        result = await self._uow.session.execute(
            select(PaymentAttemptModel.id)
            .where(PaymentAttemptModel.order_ref == order_ref, PaymentAttemptModel.status == "paid")
            .limit(1)
        )
        return result.first() is not None

    async def save(self, payment: PaymentAttempt) -> None:
        await self._uow.session.execute(
            update(PaymentAttemptModel)
            .where(PaymentAttemptModel.id == payment.id)
            .values(
                status=payment.status.value,
                authority=payment.authority,
                reference_id=payment.reference_id,
                failure_reason=payment.failure_reason,
                updated_at=payment.updated_at,
            )
        )

    async def list_reconcilable(self, *, now: datetime, stuck_for_seconds: int, limit: int) -> list[uuid.UUID]:
        stuck_before = now - timedelta(seconds=stuck_for_seconds)
        result = await self._uow.session.execute(
            select(PaymentAttemptModel.id)
            .where(
                or_(
                    and_(
                        PaymentAttemptModel.status.in_(("unknown", "verifying")),
                        PaymentAttemptModel.updated_at <= stuck_before,
                    ),
                    and_(
                        PaymentAttemptModel.status.in_(("created", "redirected")),
                        PaymentAttemptModel.expires_at <= now,
                    ),
                )
            )
            .order_by(PaymentAttemptModel.updated_at)
            .limit(limit)
        )
        return list(result.scalars())
