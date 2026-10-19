# ruff: noqa: F401, F811  (pytest fixtures are imported from the accounting flow tests and then used by name)
"""Staff members and what they are paid: every payment is booked as a payroll expense and counted for its month."""

from __future__ import annotations

import pytest

from davos.modules.accounting.domain.enums.account_role import AccountRole
from tests.integration.accounting.test_accounting_flow import TODAY, balance, code, container, role

pytestmark = pytest.mark.integration


async def test_a_payment_is_booked_as_an_expense_and_counts_against_the_months_salary(container) -> None:
    staff = container.staff()
    member = await staff.create(
        name="رضا احمدی", title="راهنمای پیست", mobile="09120000000", monthly_salary_irr=300_000_000, note=""
    )
    bank = await role(container, AccountRole.BANK)
    capital = await role(container, AccountRole.CAPITAL)
    from davos.modules.accounting.domain.value_objects.journal_line import JournalLine

    await container.journal().post_manual(
        entry_date=TODAY,
        description="سرمایه",
        lines=[JournalLine(bank, debit_irr=1_000_000_000), JournalLine(capital, credit_irr=1_000_000_000)],
        created_by="owner",
    )
    advance = await staff.pay(
        member.id,
        kind="advance",
        amount_irr=100_000_000,
        day=TODAY,
        paid_from_account_id=bank,
        note="",
        created_by="owner",
    )
    bonus = await staff.pay(
        member.id,
        kind="bonus",
        amount_irr=50_000_000,
        day=TODAY,
        paid_from_account_id=bank,
        note="عید",
        created_by="owner",
    )
    assert advance.entry_id is not None and advance.month_key == bonus.month_key
    assert await balance(container, bank) == 1_000_000_000 - 150_000_000  # both left the bank
    assert await balance(container, await code(container, "5201")) == 150_000_000  # booked on the payroll category
    month = (await staff.month(advance.month_key))[0]
    assert (month.salary_paid_irr, month.bonus_paid_irr, month.remaining_irr) == (100_000_000, 50_000_000, 200_000_000)
    assert {p.kind for p in await staff.history(member.id)} == {"advance", "bonus"}
