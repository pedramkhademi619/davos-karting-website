from __future__ import annotations

import uuid
from datetime import datetime

from davos.shared_kernel.domain.entity import Entity
from davos.shared_kernel.domain.errors.validation_error import ValidationError

MAX_SALARY_IRR = 10**12  # 100 billion Toman: a typo guard, not a business rule


class StaffMember(Entity[uuid.UUID]):
    """A person who works at the track and is paid by it: name, role, phone and the monthly salary agreed with them."""

    def __init__(
        self,
        *,
        staff_id: uuid.UUID,
        name: str,
        title: str,
        mobile: str,
        monthly_salary_irr: int,
        note: str,
        active: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(staff_id)
        self.name = self._clean_name(name)
        self.title = " ".join(title.split())[:80]
        self.mobile = mobile.strip()[:20]
        self.monthly_salary_irr = self._salary(monthly_salary_irr)
        self.note = note.strip()[:300]
        self.active = active
        self.created_at = created_at

    @classmethod
    def create(
        cls, *, name: str, title: str, mobile: str, monthly_salary_irr: int, note: str, now: datetime
    ) -> StaffMember:
        return cls(
            staff_id=uuid.uuid4(),
            name=name,
            title=title,
            mobile=mobile,
            monthly_salary_irr=monthly_salary_irr,
            note=note,
            active=True,
            created_at=now,
        )

    def edit(self, *, name: str, title: str, mobile: str, monthly_salary_irr: int, note: str, active: bool) -> None:
        self.name = self._clean_name(name)
        self.title = " ".join(title.split())[:80]
        self.mobile = mobile.strip()[:20]
        self.monthly_salary_irr = self._salary(monthly_salary_irr)
        self.note = note.strip()[:300]
        self.active = active

    @staticmethod
    def _clean_name(name: str) -> str:
        name = " ".join(name.split())
        if not name or len(name) > 120:
            raise ValidationError("نام کارمند را وارد کنید.", code="invalid_staff_name")
        return name

    @staticmethod
    def _salary(value: int) -> int:
        if not 0 <= value <= MAX_SALARY_IRR:
            raise ValidationError("حقوق ماهانه معتبر نیست.", code="invalid_salary")
        return value
