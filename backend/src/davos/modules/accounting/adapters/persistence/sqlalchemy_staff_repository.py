from __future__ import annotations

import uuid

from sqlalchemy import select, update

from davos.modules.accounting.adapters.persistence.staff_member_model import StaffMemberModel
from davos.modules.accounting.adapters.persistence.staff_payment_model import StaffPaymentModel
from davos.modules.accounting.application.ports.staff_repository import StaffRepository
from davos.modules.accounting.domain.entities.staff_member import StaffMember
from davos.modules.accounting.domain.entities.staff_payment import StaffPayment
from davos.platform.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def _member(m: StaffMemberModel) -> StaffMember:
    return StaffMember(
        staff_id=m.id,
        name=m.name,
        title=m.title,
        mobile=m.mobile,
        monthly_salary_irr=m.monthly_salary_irr,
        note=m.note,
        active=m.active,
        created_at=m.created_at,
    )


def _payment(m: StaffPaymentModel) -> StaffPayment:
    return StaffPayment(
        payment_id=m.id,
        staff_id=m.staff_id,
        kind=m.kind,
        amount_irr=m.amount_irr,
        month_key=m.month_key,
        paid_on=m.paid_on,
        note=m.note,
        entry_id=m.entry_id,
        created_by=m.created_by,
        created_at=m.created_at,
    )


class SqlAlchemyStaffRepository(StaffRepository):
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self._uow = uow

    async def add(self, member: StaffMember) -> None:
        self._uow.session.add(
            StaffMemberModel(
                id=member.id,
                name=member.name,
                title=member.title,
                mobile=member.mobile,
                monthly_salary_irr=member.monthly_salary_irr,
                note=member.note,
                active=member.active,
                created_at=member.created_at,
            )
        )
        await self._uow.session.flush()

    async def save(self, member: StaffMember) -> None:
        await self._uow.session.execute(
            update(StaffMemberModel)
            .where(StaffMemberModel.id == member.id)
            .values(
                name=member.name,
                title=member.title,
                mobile=member.mobile,
                monthly_salary_irr=member.monthly_salary_irr,
                note=member.note,
                active=member.active,
            )
        )

    async def get(self, staff_id: uuid.UUID) -> StaffMember | None:
        model = await self._uow.session.get(StaffMemberModel, staff_id)
        return _member(model) if model else None

    async def list_all(self) -> list[StaffMember]:
        result = await self._uow.session.execute(select(StaffMemberModel).order_by(StaffMemberModel.name))
        return [_member(m) for m in result.scalars()]

    async def add_payment(self, payment: StaffPayment) -> None:
        self._uow.session.add(
            StaffPaymentModel(
                id=payment.payment_id,
                staff_id=payment.staff_id,
                kind=payment.kind,
                amount_irr=payment.amount_irr,
                month_key=payment.month_key,
                paid_on=payment.paid_on,
                note=payment.note,
                entry_id=payment.entry_id,
                created_by=payment.created_by,
                created_at=payment.created_at,
            )
        )
        await self._uow.session.flush()

    async def payments_of_month(self, month_key: str) -> list[StaffPayment]:
        result = await self._uow.session.execute(
            select(StaffPaymentModel).where(StaffPaymentModel.month_key == month_key)
        )
        return [_payment(m) for m in result.scalars()]

    async def payments_of(self, staff_id: uuid.UUID, limit: int) -> list[StaffPayment]:
        result = await self._uow.session.execute(
            select(StaffPaymentModel)
            .where(StaffPaymentModel.staff_id == staff_id)
            .order_by(StaffPaymentModel.paid_on.desc(), StaffPaymentModel.created_at.desc())
            .limit(limit)
        )
        return [_payment(m) for m in result.scalars()]
