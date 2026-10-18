"""A year of believable books for the demo, the way a karting track actually keeps them: every ticket sale and refund,
the snack bar, the occasional private event, everyday expenses paid from the till or the bank in a handful of plain
categories, the weekly cash deposit, a nightly till count and the owner taking the month's profit out.

Online and card-reader money settles into the bank by itself, so it is booked straight to the bank. The whole business
is simulated day by day with running balances (the till never goes negative; what the till cannot pay comes from the
bank), and every entry is balanced before it is kept.
"""

from __future__ import annotations

import random
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from typing import Any

from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.tools.demo_data.common import at, new_id, random_clock
from davos.tools.demo_data.people import EXPENSE_NOTES, full_name

Row = dict[str, Any]
Key = str | uuid.UUID  # a role name, an account code, or an account id
Lines = list[tuple[Key, int, int, str]]
T = 10  # one Toman in Rial
M = 1_000_000 * T  # one million Toman in Rial

# The everyday categories of the default chart (codes) the demo spends and earns in.
FUEL, REPAIRS, STAFF, RENT, BILLS, ADS, SAFETY, INSURANCE, TAXES, OTHER = (
    "5101",
    "5102",
    "5201",
    "5301",
    "5302",
    "5401",
    "5105",
    "5104",
    "5502",
    "5305",
)
SNACK_BAR, EVENTS, OTHER_INCOME = "4102", "4104", "4301"
STAFF_COUNT = 14
CASH_FLOAT = 30 * M  # what stays in the till after the weekly bank deposit


def build(
    rng: random.Random,
    *,
    now: datetime,
    start: date,
    sales: list[Row],
    roles: dict[str, uuid.UUID],
    codes: dict[str, uuid.UUID],
    first_number: dict[int, int],
) -> dict[str, list[Row]]:
    """``roles`` maps role names to account ids, ``codes`` maps account codes to ids."""
    tz = at(start, time(0)).tzinfo
    today = now.astimezone(tz).date()
    out: dict[str, list[Row]] = {"entries": [], "closings": []}
    counters: dict[int, int] = defaultdict(int, first_number)
    role_of = {account_id: role for role, account_id in roles.items()}
    bal: dict[str, int] = defaultdict(int)

    def account(key: Key) -> uuid.UUID:
        if isinstance(key, uuid.UUID):
            return key
        return roles[key] if key in roles else codes[key]

    def emit(
        day: date,
        description: str,
        source: str,
        lines: Sequence[tuple[Key, int, int, str]],
        *,
        ref: str | None = None,
        source_date: date | None = None,
        by: str = "demo",
        moment: time | None = None,
    ) -> Row:
        debit = sum(line[1] for line in lines)
        credit = sum(line[2] for line in lines)
        if debit != credit or debit <= 0:
            raise AssertionError(f"unbalanced demo entry {description}: {debit} vs {credit}")
        year = FiscalCalendar.year_of(day)
        counters[year] += 1
        entry: Row = {
            "id": new_id(rng),
            "fiscal_year": year,
            "number": counters[year],
            "entry_date": day,
            "description": description[:300],
            "source": source,
            "source_ref": ref,
            "source_date": source_date,
            "status": "posted",
            "reversed_by_id": None,
            "reversal_of_id": None,
            "created_by": by,
            "created_at": at(day, moment or random_clock(rng, 10, 23)),
            "lines": [
                {"account_id": account(a), "debit_irr": d, "credit_irr": c, "memo": m[:300], "party_id": None}
                for a, d, c, m in lines
            ],
        }
        for a, d, c, _ in lines:
            role = role_of.get(account(a))
            if role:
                bal[role] += d - c
        out["entries"].append(entry)
        return entry

    def spend(day: date, description: str, category: str, amount: int, *, prefer: str = "bank") -> None:
        """An expense paid now: small ones from the till when it can spare the money, the rest from the bank."""
        amount = max(amount // (10_000 * T) * (10_000 * T), 10_000 * T)  # whole ten-thousand Toman, like real bills
        paying = "cash" if prefer == "cash" and bal["cash"] >= amount + 5 * M else "bank"
        if bal[paying] < amount:
            return
        emit(day, description, "expense", [(category, amount, 0, description), (paying, 0, amount, description)])

    def earn(day: date, description: str, category: str, amount: int, into: str) -> None:
        emit(day, description, "income", [(into, amount, 0, description), (category, 0, amount, description)])

    emit(
        start,
        "موجودی اول دوره (بانک و صندوق)",
        "opening",
        [
            ("bank", 600 * M, 0, "موجودی بانک"),
            ("cash", 15 * M, 0, "موجودی صندوق"),
            ("capital", 0, 615 * M, "سرمایه"),
        ],
        moment=time(9, 0),
    )

    sales_by_day: dict[date, list[Row]] = defaultdict(list)
    refunds_by_day: dict[date, list[Row]] = defaultdict(list)
    for sale in sales:
        sales_by_day[sale["at"].astimezone(tz).date()].append(sale)
        if sale["refunded"] and sale["refund_at"]:
            refunds_by_day[sale["refund_at"].astimezone(tz).date()].append(sale)
    refund_payouts: dict[date, list[Row]] = defaultdict(list)
    staff = [full_name(rng) for _ in range(STAFF_COUNT)]
    wages = {who: rng.randint(28, 48) * M for who in staff}

    day = start
    while day <= today:
        year, month = FiscalCalendar.month_of(day)
        month_start, month_end = FiscalCalendar.month_start(year, month), FiscalCalendar.month_end(year, month)

        # tickets: online and card money lands in the bank, cash in the till
        for sale in sorted(sales_by_day.get(day, []), key=lambda s: s["at"]):
            label = f"فروش {'آنلاین' if sale['online'] else 'حضوری'} بلیت {sale['ticket']}"
            receipt = "cash" if not sale["online"] and sale["method"] == "cash" else "bank"
            emit(
                day,
                label,
                "online_sale" if sale["online"] else "counter_sale",
                [(receipt, sale["amount"], 0, label), ("sales_revenue", 0, sale["amount"], label)],
                ref=sale["id"],
                source_date=sale["session_day"],
                by="system",
                moment=sale["at"].astimezone(tz).time(),
            )
        # a cancelled online ticket is owed back until the owner transfers the money; a counter sale is paid back on
        # the spot from where it was paid
        for sale in refunds_by_day.get(day, []):
            label = f"استرداد بلیت {sale['ticket']}"
            if sale["online"]:
                credit = "refunds_payable"
            else:
                credit = "cash" if sale["method"] == "cash" else "bank"
                if bal[credit] < sale["amount"]:
                    credit = "refunds_payable"
            emit(
                day,
                label,
                "refund",
                [("sales_returns", sale["amount"], 0, label), (credit, 0, sale["amount"], label)],
                ref=sale["id"],
                source_date=sale["session_day"],
                by="system",
            )
            if credit == "refunds_payable":
                refund_payouts[day + timedelta(days=rng.randint(1, 3))].append(sale)
        for sale in refund_payouts.pop(day, []):
            if bal["bank"] >= sale["amount"]:
                label = f"پرداخت استرداد بلیت {sale['ticket']}"
                emit(
                    day,
                    label,
                    "transfer",
                    [("refunds_payable", sale["amount"], 0, label), ("bank", 0, sale["amount"], label)],
                )

        # the snack bar every day the track is busy, private events now and then
        volume = len(sales_by_day.get(day, []))
        if volume:
            earn(day, "فروش بوفه", SNACK_BAR, volume * rng.randint(40, 110) * 1_000 * T, "cash")
        if day.weekday() in (3, 4) and rng.random() < 0.25:
            kind = rng.choice(["جشن تولد", "رویداد شرکتی", "مسابقه دوستانه"])
            earn(
                day, f"{kind} ({full_name(rng)})", EVENTS, rng.randint(8, 40) * M, rng.choice(["bank", "bank", "cash"])
            )
        if rng.random() < 0.02:
            earn(
                day,
                rng.choice(["اجاره پیست برای فیلم‌برداری", "فروش قطعات مستعمل"]),
                OTHER_INCOME,
                rng.randint(5, 30) * M,
                "bank",
            )

        # everyday spending, sized for a track that sells about 2.5 billion Toman of tickets a month
        if (day - start).days % 3 == 0:
            spend(day, rng.choice(EXPENSE_NOTES["fuel"]), FUEL, rng.randint(3, 7) * M, prefer="cash")
        if day.weekday() not in (3, 4) and rng.random() < 0.5:
            note = rng.choice(EXPENSE_NOTES["repair"] + EXPENSE_NOTES["oil"])
            spend(day, note, REPAIRS, rng.randint(5, 30) * M, prefer="cash" if rng.random() < 0.3 else "bank")
        if day == month_start + timedelta(days=4):
            spend(day, rng.choice(EXPENSE_NOTES["tyre"]), REPAIRS, rng.randint(60, 120) * M)
        if rng.random() < 0.6:
            note = rng.choice(EXPENSE_NOTES["cleaning"] + EXPENSE_NOTES["office"] + EXPENSE_NOTES["food"])
            spend(day, note, OTHER, rng.randint(5, 60) * 100_000 * T, prefer="cash")
        if day.weekday() == 0:
            spend(day, "خرید بوفه (نوشیدنی و تنقلات)", OTHER, rng.randint(15, 30) * M, prefer="cash")
        if day.weekday() == 6:
            spend(day, rng.choice(EXPENSE_NOTES["marketing"]), ADS, rng.randint(15, 40) * M)
        if day == month_start:
            spend(day, "اجاره ماهانه پیست", RENT, 350 * M)
            if month in (1, 4, 7, 10):
                spend(day, rng.choice(EXPENSE_NOTES["insurance"]), INSURANCE, rng.randint(150, 250) * M)
        if day == month_start + timedelta(days=9) and rng.random() < 0.7:
            spend(day, rng.choice(EXPENSE_NOTES["ppe"]), SAFETY, rng.randint(20, 50) * M)
        if day == month_start + timedelta(days=14):
            for name, low, high in (("قبض برق", 30, 60), ("قبض آب", 3, 6), ("قبض گاز", 2, 8), ("تلفن و اینترنت", 3, 5)):
                spend(day, name, BILLS, rng.randint(low, high) * M)
        if day == month_start + timedelta(days=20) and month in (3, 9):
            spend(day, "مالیات و عوارض شهرداری", TAXES, rng.randint(300, 600) * M)
        if day == month_end:
            for who in staff:
                spend(day, f"حقوق {year}/{month:02d} - {who}", STAFF, wages[who])
        # the owner takes the month's profit out of the bank, keeping a cushion for the next month's bills
        if day == month_start + timedelta(days=5) and day > start + timedelta(days=40):
            draw = min(rng.randint(500, 800) * M, (bal["bank"] - 1_200 * M) // (10 * M) * (10 * M))
            if draw > 0:
                label = "برداشت سود توسط مالک"
                emit(day, label, "manual", [("capital", draw, 0, label), ("bank", 0, draw, label)])

        # the till: deposit the extra cash every Saturday, count it every night
        if day.weekday() == 5:
            deposit = (bal["cash"] - CASH_FLOAT) // M * M
            if deposit > 0:
                label = "واریز صندوق به بانک"
                emit(day, label, "transfer", [("bank", deposit, 0, label), ("cash", 0, deposit, label)])
        expected = bal["cash"]
        diff = 0 if rng.random() < 0.8 else rng.choice([-1, 1]) * rng.randint(1, 20) * 10_000 * T
        if expected + diff < 0:
            diff = 0
        entry_id = None
        if diff:
            memo = f"{'اضافه' if diff > 0 else 'کسری'} صندوق {day.isoformat()}"
            lines: Lines = (
                [("cash", diff, 0, memo), ("cash_difference", 0, diff, memo)]
                if diff > 0
                else [("cash_difference", -diff, 0, memo), ("cash", 0, -diff, memo)]
            )
            gap = emit(day, memo, "cash_close", lines, ref=day.isoformat(), moment=time(23, 55))
            entry_id = gap["id"]
        out["closings"].append(
            {
                "id": new_id(rng),
                "day": day,
                "expected_irr": expected,
                "counted_irr": expected + diff,
                "entry_id": entry_id,
                "note": "",
                "closed_by": "demo-staff",
                "created_at": at(day, time(23, 58)),
            }
        )
        day += timedelta(days=1)

    out["counters"] = [{"key": f"journal:{y}", "value": n} for y, n in counters.items()]
    return out
