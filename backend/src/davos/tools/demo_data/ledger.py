"""A year of believable books for the demo: every ticket sale and refund, expenses on credit and in cash, supplier
bills and payments, weekly bank deposits and gateway settlements, daily till counts, asset purchases with monthly
depreciation, budgets and the closing of last fiscal year.

The whole business is simulated day by day with running balances (the till never goes negative; what cannot be paid
in cash is paid from the bank), and every entry is balanced before it is kept.
"""

from __future__ import annotations

import random
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from typing import Any

from davos.modules.accounting.domain.entities.fixed_asset import FixedAsset
from davos.modules.accounting.domain.enums.asset_status import AssetStatus
from davos.modules.accounting.domain.services.depreciation_calculator import DepreciationCalculator
from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.tools.demo_data.common import at, new_id, random_clock
from davos.tools.demo_data.people import EXPENSE_NOTES, VENDORS, full_name

Row = dict[str, Any]
Key = str | uuid.UUID  # a role name, an account code, or an account id
Lines = list[tuple[Key, int, int, str, uuid.UUID | None]]
T = 10  # one Toman in Rial

# code, name, type, parent code: extra leaf accounts so the chart looks lived-in
EXTRA_ACCOUNTS: list[tuple[str, str, str, str]] = [
    ("1205", "سیستم زمان‌سنجی و تایمینگ", "asset", "12"),
    ("1206", "تجهیزات صوتی و روشنایی", "asset", "12"),
    ("1207", "بهسازی و دکوراسیون پیست", "asset", "12"),
    ("2107", "وام بانکی کوتاه‌مدت", "liability", "21"),
    ("4105", "فروش سوغات و محصولات", "revenue", "41"),
    ("4106", "درآمد برگزاری جشن تولد", "revenue", "41"),
    ("5106", "روغن، فیلتر و مواد مصرفی خودرو", "expense", "51"),
    ("5107", "شستشو و نظافت خودروها", "expense", "51"),
    ("5204", "آموزش و گواهی پرسنل", "expense", "52"),
    ("5205", "غذا و پذیرایی پرسنل", "expense", "52"),
    ("5306", "تعمیر و نگهداری ساختمان", "expense", "53"),
    ("5307", "حمل و نقل و پست", "expense", "53"),
    ("5403", "چاپ و تبلیغات محیطی", "expense", "54"),
    ("5404", "تبلیغات آنلاین و شبکه‌های اجتماعی", "expense", "54"),
    ("5505", "جرایم و خسارت‌ها", "expense", "55"),
]

# (name, type code, count, cost range in Toman, life months, first purchase day offset range)
ASSET_PLAN: list[tuple[str, str, int, tuple[int, int], int, tuple[int, int]]] = [
    ("کارت تک‌نفره", "1201", 14, (380_000_000, 520_000_000), 60, (0, 20)),
    ("کارت دونفره", "1201", 4, (650_000_000, 820_000_000), 72, (0, 25)),
    ("سیستم زمان‌سنجی", "1205", 1, (180_000_000, 180_000_000), 48, (5, 5)),
    ("سیستم صوتی پیست", "1206", 2, (60_000_000, 95_000_000), 60, (10, 40)),
    ("نورپردازی مسیر", "1206", 3, (45_000_000, 80_000_000), 60, (10, 60)),
    ("دکوراسیون و سایبان", "1207", 3, (150_000_000, 400_000_000), 96, (0, 30)),
    ("تجهیزات ایمنی و حفاظ", "1203", 6, (20_000_000, 90_000_000), 48, (0, 90)),
    ("تجهیزات ورزشی و کلاه", "1203", 5, (15_000_000, 70_000_000), 36, (0, 120)),
    ("اثاثیه پذیرش", "1204", 4, (8_000_000, 40_000_000), 60, (0, 40)),
    ("رایانه و پرینتر", "1204", 3, (25_000_000, 60_000_000), 48, (0, 60)),
    ("کارت تک‌نفره (خرید جدید)", "1201", 2, (500_000_000, 560_000_000), 60, (260, 330)),
]


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
    """``roles`` maps role names to account ids, ``codes`` maps account codes to ids (including the extra accounts)."""
    today = now.astimezone(at(start, time(0)).tzinfo).date()
    out: dict[str, list[Row]] = {k: [] for k in ("vendors", "entries", "assets", "runs", "budgets", "closings")}
    counters: dict[int, int] = defaultdict(int, first_number)
    role_of = {account_id: role for role, account_id in roles.items()}
    bal: dict[str, int] = defaultdict(int)
    payable_by_vendor: dict[uuid.UUID, int] = defaultdict(int)

    vendors: list[Row] = []
    for index, name in enumerate(VENDORS):
        row: Row = {
            "id": new_id(rng),
            "name": name,
            "phone": "07136" + "".join(str(rng.randint(0, 9)) for _ in range(6)),
            "note": "",
            "active": index < len(VENDORS) - 3,
            "created_at": at(start - timedelta(days=rng.randint(0, 40)), random_clock(rng, 9, 17)),
        }
        vendors.append(row)
    out["vendors"] = vendors
    vendor_ids: dict[str, uuid.UUID] = {name: v["id"] for name, v in zip(VENDORS, vendors, strict=True)}

    def pick(*names: str) -> uuid.UUID:
        return vendor_ids[rng.choice(names)]

    fuel_vendors = ("پمپ بنزین نارنجستان", "پمپ بنزین بلوار مدرس")
    part_vendors = (
        "قطعات یدکی کارت پارس",
        "تعمیرگاه سرعت",
        "تأمین‌کننده قطعات موتور",
        "گیربکس‌سازی ماهان",
        "ترمز و کلاچ پیشرو",
        "باتری سازان",
    )

    def emit(
        day: date,
        description: str,
        source: str,
        lines: Sequence[tuple[Key, int, int, str, uuid.UUID | None]],
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
            "created_at": at(day, moment or random_clock(rng, 9, 23)),
            "lines": [
                {"account_id": codes_or_roles(a), "debit_irr": d, "credit_irr": c, "memo": m[:300], "party_id": p}
                for a, d, c, m, p in lines
            ],
        }
        for a, d, c, _, _ in lines:
            role = role_of.get(codes_or_roles(a))
            if role:
                bal[role] += d - c
        out["entries"].append(entry)
        return entry

    def codes_or_roles(key: Key) -> uuid.UUID:
        if isinstance(key, uuid.UUID):
            return key
        return roles[key] if key in roles else codes[key]

    # ------------------------------------------------------------------ opening capital and assets
    emit(
        start,
        "افتتاحیه: آورده نقدی صاحب سرمایه",
        "opening",
        [("bank", 180_000_000_000, 0, "آورده نقدی", None), ("capital", 0, 180_000_000_000, "سرمایه اولیه", None)],
        moment=time(9, 0),
    )
    assets: list[FixedAsset] = []
    purchases: list[tuple[date, Row, str]] = []
    for name, code, count, cost_range, life, offset in ASSET_PLAN:
        for index in range(count):
            in_service = start + timedelta(days=rng.randint(*offset))
            if in_service > today - timedelta(days=5):
                in_service = today - timedelta(days=rng.randint(30, 60))
            cost = rng.randint(cost_range[0] // 1_000_000, cost_range[1] // 1_000_000) * 1_000_000 * T
            label = f"{name} {index + 1}" if count > 1 else name
            planned = FixedAsset(
                asset_id=new_id(rng),
                name=label,
                asset_account_id=codes[code],
                cost_irr=cost,
                salvage_irr=cost // 10,
                in_service_date=in_service,
                life_months=life,
                status=AssetStatus.ACTIVE,
                note="",
                created_at=at(in_service, time(10)),
            )
            assets.append(planned)
            purchases.append((in_service, {"asset": planned, "code": code}, label))
            out["assets"].append(
                {
                    "id": planned.id,
                    "name": planned.name,
                    "asset_account_id": planned.asset_account_id,
                    "cost_irr": cost,
                    "salvage_irr": planned.salvage_irr,
                    "in_service_date": in_service,
                    "life_months": life,
                    "status": "active",
                    "note": "",
                    "created_at": planned.created_at,
                }
            )
    purchases.sort(key=lambda p: p[0])
    purchase_by_day: dict[date, list[tuple[Row, str]]] = defaultdict(list)
    for day, info, label in purchases:
        purchase_by_day[day].append((info, label))

    # ------------------------------------------------------------------ the simulation, day by day
    sales_by_day: dict[date, list[Row]] = defaultdict(list)
    refunds_by_day: dict[date, list[Row]] = defaultdict(list)
    tz = at(start, time(0)).tzinfo
    for sale in sales:
        sales_by_day[sale["at"].astimezone(tz).date()].append(sale)
        if sale["refunded"] and sale["refund_at"]:
            refunds_by_day[sale["refund_at"].astimezone(tz).date()].append(sale)
    refund_payouts: dict[date, list[int]] = defaultdict(list)
    open_bills: list[Row] = []
    gateway_in: dict[date, int] = defaultdict(int)
    pos_in: dict[date, int] = defaultdict(int)

    def spend(
        day: date,
        source: str,
        description: str,
        expense_code: str,
        amount: int,
        *,
        vat: int = 0,
        vendor: uuid.UUID | None = None,
        on_credit: bool = False,
        prefer: str = "bank",
        due: int = 20,
    ) -> None:
        net = amount - vat
        lines: Lines = [(expense_code, net, 0, description, vendor)]
        if vat:
            lines.append(("vat_receivable", vat, 0, description, None))
        if on_credit and vendor is not None:
            lines.append(("payables", 0, amount, description, vendor))
            emit(day, description, source, lines)
            payable_by_vendor[vendor] += amount
            open_bills.append(
                {
                    "vendor": vendor,
                    "left": amount,
                    "due": day + timedelta(days=due + rng.randint(-5, 15)),
                    "name": description,
                }
            )
            return
        paying = (
            prefer if bal[prefer] >= amount + (20_000_000 * T if prefer == "cash" else 1_000_000_000 * T) else "bank"
        )
        if bal[paying] < amount:
            lines = [(expense_code, net, 0, description, vendor)]
            if vat:
                lines.append(("vat_receivable", vat, 0, description, None))
            if vendor is None:
                return
            lines.append(("payables", 0, amount, description, vendor))
            emit(day, description, source, lines)
            payable_by_vendor[vendor] += amount
            open_bills.append({"vendor": vendor, "left": amount, "due": day + timedelta(days=15), "name": description})
            return
        lines.append((paying, 0, amount, description, vendor))
        emit(day, description, source, lines)

    day = start
    while day <= today:
        year, month = FiscalCalendar.month_of(day)
        month_start, month_end = FiscalCalendar.month_start(year, month), FiscalCalendar.month_end(year, month)

        for info, label in purchase_by_day.get(day, []):
            asset: FixedAsset = info["asset"]
            if bal["bank"] >= asset.cost_irr:
                emit(
                    day,
                    f"خرید دارایی: {label}",
                    "asset_purchase",
                    [(info["code"], asset.cost_irr, 0, label, None), ("bank", 0, asset.cost_irr, label, None)],
                    ref=str(asset.id),
                )
            else:
                vendor = pick(*part_vendors)
                emit(
                    day,
                    f"خرید نسیه دارایی: {label}",
                    "asset_purchase",
                    [(info["code"], asset.cost_irr, 0, label, vendor), ("payables", 0, asset.cost_irr, label, vendor)],
                    ref=str(asset.id),
                )
                payable_by_vendor[vendor] += asset.cost_irr
                open_bills.append(
                    {"vendor": vendor, "left": asset.cost_irr, "due": day + timedelta(days=45), "name": label}
                )

        # tickets sold and refunded
        for sale in sorted(sales_by_day.get(day, []), key=lambda s: s["at"]):
            label = f"فروش {'آنلاین' if sale['online'] else 'حضوری'} بلیت {sale['ticket']}"
            receipt = (
                "gateway" if sale["online"] else {"cash": "cash", "card": "pos", "transfer": "bank"}[sale["method"]]
            )
            emit(
                day,
                label,
                "online_sale" if sale["online"] else "counter_sale",
                [(receipt, sale["amount"], 0, label, None), ("sales_revenue", 0, sale["amount"], label, None)],
                ref=sale["id"],
                source_date=sale["session_day"],
                by="system",
                moment=sale["at"].astimezone(tz).time(),
            )
            if sale["online"]:
                gateway_in[day] += sale["amount"]
            elif sale["method"] == "card":
                pos_in[day] += sale["amount"]
        for sale in refunds_by_day.get(day, []):
            label = f"استرداد بلیت {sale['ticket']}"
            credit = (
                "refunds_payable"
                if sale["online"]
                else {"cash": "cash", "card": "pos", "transfer": "bank"}[sale["method"]]
            )
            if not sale["online"] and bal[credit] < sale["amount"]:
                credit = "refunds_payable"
            emit(
                day,
                label,
                "refund",
                [("sales_returns", sale["amount"], 0, label, None), (credit, 0, sale["amount"], label, None)],
                ref=sale["id"],
                source_date=sale["session_day"],
                by="system",
            )
            if credit == "refunds_payable":
                refund_payouts[day + timedelta(days=rng.randint(1, 4))].append(sale["amount"])
        for amount in refund_payouts.pop(day, []):
            if bal["bank"] >= amount:
                emit(
                    day,
                    "پرداخت استرداد وجه به مشتری",
                    "transfer",
                    [("refunds_payable", amount, 0, "استرداد", None), ("bank", 0, amount, "استرداد", None)],
                )

        # the snack bar and other income
        volume = len(sales_by_day.get(day, []))
        if volume:
            snack = volume * rng.randint(40, 110) * 10_000
            emit(
                day,
                "فروش روزانه بوفه",
                "income",
                [("cash", snack * T // 10, 0, "بوفه", None), ("4102", 0, snack * T // 10, "بوفه", None)],
            )
            if rng.random() < 0.12:
                gift = rng.randint(2, 15) * 1_000_000 * T
                emit(
                    day,
                    "فروش سوغات و محصولات",
                    "income",
                    [("cash", gift, 0, "فروش", None), ("4105", 0, gift, "فروش", None)],
                )
        if day.weekday() in (3, 4) and rng.random() < 0.3:
            party = rng.randint(8, 40) * 1_000_000 * T
            emit(
                day,
                f"برگزاری جشن تولد ({full_name(rng)})",
                "income",
                [("bank" if rng.random() < 0.5 else "cash", party, 0, "جشن", None), ("4106", 0, party, "جشن", None)],
            )
        if rng.random() < 0.04:
            sponsor = rng.randint(30, 120) * 1_000_000 * T
            vat = sponsor // 11 if rng.random() < 0.4 else 0
            lines: Lines = [("bank", sponsor, 0, "اسپانسر", None), ("4103", 0, sponsor - vat, "اسپانسر", None)]
            if vat:
                lines.append(("vat_payable", 0, vat, "اسپانسر", None))
            emit(
                day,
                f"درآمد اسپانسر ({rng.choice(['برند نوشیدنی', 'فروشگاه لوازم ورزشی', 'بانک', 'شرکت بیمه'])})",
                "income",
                lines,
            )

        # operating expenses
        if rng.random() < 0.55:
            note = rng.choice(EXPENSE_NOTES["cleaning"] + EXPENSE_NOTES["office"] + EXPENSE_NOTES["food"])
            code = {"cleaning": "5304", "office": "5305", "food": "5205"}[
                next(k for k in ("cleaning", "office", "food") if note in EXPENSE_NOTES[k])
            ]
            spend(day, "expense", note, code, rng.randint(3, 40) * 100_000 * T, prefer="cash")
        if (day - start).days % 3 == 0:
            amount = rng.randint(15, 45) * 1_000_000 * T
            spend(
                day,
                "expense",
                rng.choice(EXPENSE_NOTES["fuel"]),
                "5101",
                amount,
                vendor=pick(*fuel_vendors),
                on_credit=rng.random() < 0.65,
                due=14,
            )
        if day.weekday() not in (3, 4) and rng.random() < 0.5:
            amount = rng.randint(2, 60) * 1_000_000 * T
            vat = amount // 11 if rng.random() < 0.4 else 0
            spend(
                day,
                "expense",
                rng.choice(EXPENSE_NOTES["repair"]),
                "5102",
                amount,
                vat=vat,
                vendor=pick(*part_vendors),
                on_credit=rng.random() < 0.5,
                due=21,
            )
        if rng.random() < 0.1:
            amount = rng.randint(20, 120) * 1_000_000 * T
            kind = rng.choice(["tyre", "oil"])
            spend(
                day,
                "expense",
                rng.choice(EXPENSE_NOTES[kind]),
                "5103" if kind == "tyre" else "5106",
                amount,
                vat=amount // 11,
                vendor=pick("لاستیک فروشی ایران‌تایر", "شرکت روغن موتور زرین"),
                on_credit=rng.random() < 0.6,
                due=30,
            )
        if day.weekday() == 6:
            spend(
                day,
                "expense",
                rng.choice(EXPENSE_NOTES["marketing"]),
                rng.choice(["5401", "5403", "5404"]),
                rng.randint(10, 40) * 1_000_000 * T,
                vendor=pick("تبلیغات رسانه نو", "چاپخانه نگار"),
                on_credit=rng.random() < 0.3,
            )
        if rng.random() < 0.05:
            spend(
                day,
                "expense",
                rng.choice(["هزینه ایمنی و آتش‌نشانی", "جریمه شهرداری", "خسارت به خودرو مشتری"]),
                "5505",
                rng.randint(2, 25) * 1_000_000 * T,
                prefer="bank",
            )
        if day == month_start:
            spend(day, "expense", "اجاره ماهانه پیست", "5301", 150_000_000 * T)
            spend(
                day,
                "expense",
                "اینترنت و سرور سایت",
                "5303",
                rng.randint(2, 6) * 1_000_000 * T,
                vendor=pick("اینترنت پارس‌آنلاین", "نرم‌افزار سامانه‌گستر"),
            )
            if month in (1, 4, 7, 10):
                spend(
                    day,
                    "expense",
                    "بیمه خودروها و پیست",
                    "5104",
                    90_000_000 * T,
                    vendor=pick("ایمن‌بیمه"),
                    on_credit=True,
                    due=25,
                )
        if day == month_start + timedelta(days=14):
            for name, code, low, high in (
                ("قبض برق", "5302", 12, 25),
                ("قبض آب", "5302", 2, 4),
                ("قبض گاز", "5302", 3, 8),
                ("قبض تلفن", "5302", 1, 2),
            ):
                spend(day, "expense", name, code, rng.randint(low, high) * 1_000_000 * T)
        if day == month_end:
            for _ in range(8):
                pay = rng.randint(22, 45) * 1_000_000 * T
                who = full_name(rng)
                if bal["bank"] >= pay:
                    emit(
                        day,
                        f"حقوق {year}/{month:02d} - {who}",
                        "payroll",
                        [("5201", pay, 0, f"حقوق {who}", None), ("bank", 0, pay, f"حقوق {who}", None)],
                    )
            if rng.random() < 0.5:
                spend(day, "expense", "پاداش و اضافه‌کار", "5203", rng.randint(10, 40) * 1_000_000 * T)

        # supplier bills fall due
        for bill in list(open_bills):
            if bill["due"] <= day and bill["left"] > 0:
                pay = bill["left"] if rng.random() < 0.8 else bill["left"] // 2 // T * T
                if pay <= 0:
                    continue
                source = "cash" if pay <= 5_000_000 * T and bal["cash"] > pay + 20_000_000 * T else "bank"
                if bal[source] < pay:
                    bill["due"] = day + timedelta(days=7)
                    continue
                emit(
                    day,
                    f"پرداخت به تامین‌کننده: {bill['name']}",
                    "vendor_payment",
                    [
                        ("payables", pay, 0, bill["name"], bill["vendor"]),
                        (source, 0, pay, bill["name"], bill["vendor"]),
                    ],
                )
                bill["left"] -= pay
                payable_by_vendor[bill["vendor"]] -= pay
                if bill["left"] <= 0:
                    open_bills.remove(bill)
                else:
                    bill["due"] = day + timedelta(days=rng.randint(5, 25))

        # banking: deposit the till, settle the card reader and the gateway
        if day.weekday() == 5:
            keep = sum(gateway_in[day - timedelta(days=k)] for k in range(0, 2))
            settle = bal["gateway"] - keep
            if settle > 0:
                emit(
                    day,
                    "تسویه درگاه پرداخت به حساب بانکی",
                    "transfer",
                    [("bank", settle, 0, "تسویه درگاه", None), ("gateway", 0, settle, "تسویه درگاه", None)],
                )
            settle_pos = bal["pos"] - sum(pos_in[day - timedelta(days=k)] for k in range(0, 2))
            if settle_pos > 0:
                emit(
                    day,
                    "تسویه کارت‌خوان به حساب بانکی",
                    "transfer",
                    [("bank", settle_pos, 0, "تسویه کارت‌خوان", None), ("pos", 0, settle_pos, "تسویه کارت‌خوان", None)],
                )
            deposit = bal["cash"] - 30_000_000 * T
            if deposit > 0:
                deposit = deposit // (1_000_000 * T) * (1_000_000 * T)
                if deposit > 0:
                    emit(
                        day,
                        "واریز موجودی صندوق به بانک",
                        "transfer",
                        [("bank", deposit, 0, "واریز نقدی", None), ("cash", 0, deposit, "واریز نقدی", None)],
                    )

        # the till is counted every night
        expected = bal["cash"]
        diff = 0 if rng.random() < 0.62 else rng.choice([-1, 1]) * rng.randint(1, 60) * 5_000 * T
        if expected + diff < 0:
            diff = 0
        entry_id = None
        if diff:
            memo = f"{'اضافه' if diff > 0 else 'کسری'} صندوق {day.isoformat()}"
            gap = emit(
                day,
                memo,
                "cash_close",
                [("cash", diff, 0, memo, None), ("cash_difference", 0, diff, memo, None)]
                if diff > 0
                else [("cash_difference", -diff, 0, memo, None), ("cash", 0, -diff, memo, None)],
                ref=day.isoformat(),
                moment=time(23, 55),
            )
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

        # depreciation at the end of each Jalali month
        if day == month_end:
            running = []
            key = FiscalCalendar.month_key(year, month)
            for asset in assets:
                already = sum(r["amount_irr"] for r in out["runs"] if r["asset_id"] == asset.id)
                amount = DepreciationCalculator.amount_for_month(asset, year, month, already)
                if amount > 0:
                    running.append((asset, amount))
            total = sum(a for _, a in running)
            if total:
                entry = emit(
                    day,
                    f"استهلاک ماه {key}",
                    "depreciation",
                    [
                        ("depreciation_expense", total, 0, "استهلاک", None),
                        ("accumulated_depreciation", 0, total, "استهلاک", None),
                    ],
                    ref=key,
                    moment=time(23, 59),
                )
                for asset, amount in running:
                    out["runs"].append(
                        {"asset_id": asset.id, "month_key": key, "amount_irr": amount, "entry_id": entry["id"]}
                    )

        # last fiscal year is closed (profit moves to retained earnings) once it has ended
        if day == FiscalCalendar.year_end(year) and year < FiscalCalendar.year_of(today):
            nets: dict[uuid.UUID, int] = defaultdict(int)
            temporary = {codes[c] for c in codes if c[:1] in ("4", "5")}
            for entry in out["entries"]:
                if entry["fiscal_year"] == year and entry["source"] != "closing":
                    for line in entry["lines"]:
                        if line["account_id"] in temporary:
                            nets[line["account_id"]] += line["debit_irr"] - line["credit_irr"]
            lines2: Lines = [
                (k, 0 if v > 0 else -v, v if v > 0 else 0, f"بستن حساب‌های سال {year}", None)
                for k, v in nets.items()
                if v
            ]
            profit = -sum(nets.values())
            if lines2:
                lines2.append(
                    (
                        "retained_earnings",
                        -profit if profit < 0 else 0,
                        profit if profit > 0 else 0,
                        f"سود (زیان) سال {year}",
                        None,
                    )
                )
                emit(
                    day,
                    f"بستن حساب‌های موقت سال {year}",
                    "closing",
                    lines2,
                    ref=str(year),
                    by="owner",
                    moment=time(23, 59),
                )
                out["lock"] = [{"locked_through": day}]
        day += timedelta(days=1)

    # budgets for the current and the previous fiscal year (Rial per month)
    plan = {
        "4101": 1_400_000_000,
        "4102": 120_000_000,
        "5101": 180_000_000,
        "5102": 160_000_000,
        "5201": 320_000_000,
        "5301": 150_000_000,
        "5302": 40_000_000,
        "5401": 60_000_000,
        "5303": 6_000_000,
    }
    for year in {FiscalCalendar.year_of(start), FiscalCalendar.year_of(today)}:
        for code, monthly in plan.items():
            for month in range(1, 13):
                if year == FiscalCalendar.year_of(start) and month < FiscalCalendar.month_of(start)[1]:
                    continue
                out["budgets"].append(
                    {
                        "account_id": codes[code],
                        "year": year,
                        "month": month,
                        "amount_irr": int(monthly * T * rng.uniform(0.92, 1.12)),
                    }
                )
    out["counters"] = [{"key": f"journal:{y}", "value": n} for y, n in counters.items()]
    return out
