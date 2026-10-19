from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from davos.modules.accounting.application.ports.account_repository import AccountRepository
from davos.modules.accounting.application.ports.staff_repository import StaffRepository
from davos.modules.accounting.application.use_cases.bookkeeping_use_case import BookkeepingUseCase
from davos.modules.accounting.domain.entities.staff_member import StaffMember
from davos.modules.accounting.domain.entities.staff_payment import PAYMENT_KINDS, StaffPayment
from davos.modules.accounting.domain.enums.account_type import AccountType
from davos.modules.accounting.domain.errors.staff_not_found_error import StaffNotFoundError
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.shared_kernel.application.clock import Clock
from davos.shared_kernel.application.unit_of_work import UnitOfWork
from davos.shared_kernel.domain.errors.validation_error import ValidationError

PAYROLL_CATEGORY_CODE = "5201"  # "حقوق و بیمه پرسنل" in the default chart


@dataclass(frozen=True)
class StaffMonth:
    """A staff member and what was paid for a month: salary and advances count against the salary, a bonus does not."""

    member: StaffMember
    month_key: str
    salary_paid_irr: int  # salary + advance
    bonus_paid_irr: int

    @property
    def remaining_irr(self) -> int:
        return max(0, self.member.monthly_salary_irr - self.salary_paid_irr)


class StaffUseCase:
    """The people who work at the track and what they are paid. Every payment is booked as a payroll expense."""

    def __init__(
        self,
        *,
        uow: UnitOfWork,
        staff: StaffRepository,
        accounts: AccountRepository,
        bookkeeping: BookkeepingUseCase,
        clock: Clock,
    ) -> None:
        self._uow = uow
        self._staff = staff
        self._accounts = accounts
        self._bookkeeping = bookkeeping
        self._clock = clock

    async def month(self, month_key: str) -> list[StaffMonth]:
        async with self._uow:
            members = await self._staff.list_all()
            payments = await self._staff.payments_of_month(month_key)
        salary: dict[uuid.UUID, int] = {}
        bonus: dict[uuid.UUID, int] = {}
        for p in payments:
            target = bonus if p.kind == "bonus" else salary
            target[p.staff_id] = target.get(p.staff_id, 0) + p.amount_irr
        return [StaffMonth(m, month_key, salary.get(m.id, 0), bonus.get(m.id, 0)) for m in members]

    async def history(self, staff_id: uuid.UUID, limit: int = 24) -> list[StaffPayment]:
        async with self._uow:
            if await self._staff.get(staff_id) is None:
                raise StaffNotFoundError
            return await self._staff.payments_of(staff_id, limit)

    async def create(self, *, name: str, title: str, mobile: str, monthly_salary_irr: int, note: str) -> StaffMember:
        async with self._uow:
            member = StaffMember.create(
                name=name,
                title=title,
                mobile=mobile,
                monthly_salary_irr=monthly_salary_irr,
                note=note,
                now=self._clock.now(),
            )
            await self._staff.add(member)
            await self._uow.commit()
        return member

    async def update(
        self,
        staff_id: uuid.UUID,
        *,
        name: str,
        title: str,
        mobile: str,
        monthly_salary_irr: int,
        note: str,
        active: bool,
    ) -> StaffMember:
        async with self._uow:
            member = await self._staff.get(staff_id)
            if member is None:
                raise StaffNotFoundError
            member.edit(
                name=name, title=title, mobile=mobile, monthly_salary_irr=monthly_salary_irr, note=note, active=active
            )
            await self._staff.save(member)
            await self._uow.commit()
        return member

    async def pay(
        self,
        staff_id: uuid.UUID,
        *,
        kind: str,
        amount_irr: int,
        day: date,
        paid_from_account_id: uuid.UUID,
        note: str,
        created_by: str,
    ) -> StaffPayment:
        """Pays a staff member and books it as an expense from the till or the bank, for the month of ``day``."""
        if kind not in PAYMENT_KINDS:
            raise ValidationError("نوع پرداخت معتبر نیست.", code="invalid_payment_kind")
        async with self._uow:
            member = await self._staff.get(staff_id)
            if member is None:
                raise StaffNotFoundError
            categories = [a for a in await self._accounts.list_all() if a.type is AccountType.EXPENSE and a.postable]
            payroll = next((a for a in categories if a.code == PAYROLL_CATEGORY_CODE), None) or next(
                (a for a in categories if "حقوق" in a.name), None
            )
        if payroll is None:
            raise ValidationError("دسته‌ی «حقوق» در حسابداری پیدا نشد؛ آن را در بخش دسته‌ها بسازید.", code="no_payroll")
        entry = await self._bookkeeping.record_expense(
            day=day,
            expense_account_id=payroll.id,
            amount_irr=amount_irr,
            vat_irr=0,
            paid_from_account_id=paid_from_account_id,
            vendor_id=None,
            description=f"{PAYMENT_KINDS[kind]} {member.name}" + (f" ({note.strip()})" if note.strip() else ""),
            created_by=created_by,
        )
        year, month = FiscalCalendar.month_of(day)
        payment = StaffPayment(
            payment_id=uuid.uuid4(),
            staff_id=staff_id,
            kind=kind,
            amount_irr=amount_irr,
            month_key=FiscalCalendar.month_key(year, month),
            paid_on=day,
            note=note.strip()[:300],
            entry_id=entry.id,
            created_by=created_by,
            created_at=self._clock.now(),
        )
        async with self._uow:
            await self._staff.add_payment(payment)
            await self._uow.commit()
        return payment
