from __future__ import annotations

from dataclasses import dataclass

from davos.modules.accounting.domain.entities.staff_member import StaffMember


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
