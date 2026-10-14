"""Fill the database with tens of thousands of believable fake rows (everything except user accounts).

    docker compose run --rm --no-deps api python -m davos.tools.seed_demo_data            # add the data
    docker compose run --rm --no-deps api python -m davos.tools.seed_demo_data --clear    # remove it again

The accounting books get the most care: a year of ticket sales, expenses, supplier bills and payments, bank deposits,
till counts, asset purchases with depreciation, budgets and a closed fiscal year, all balanced and consistent with the
reservations and payments created next to them. Every demo row can be recognised, so ``--clear`` removes exactly it.
"""

from __future__ import annotations

import argparse
import asyncio
import random
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from davos.modules.accounting.domain.services.fiscal_calendar import FiscalCalendar
from davos.platform.settings.app_settings import AppSettings
from davos.tools.demo_data import bookings, extras, ledger
from davos.tools.demo_data.common import MARK_SUFFIX, TEHRAN, at, new_id
from davos.tools.demo_data.people import CAMPAIGNS
from davos.tools.demo_data.writer import clear_demo_data, insert_rows

Row = dict[str, Any]


async def _scalar(conn: AsyncConnection, sql: str, **params: Any) -> Any:
    return (await conn.execute(text(sql), params)).scalar_one_or_none()


async def _seed(conn: AsyncConnection, *, seed: int, scale: float, now: datetime) -> dict[str, int]:
    rng = random.Random(seed)
    counts: dict[str, int] = {}
    if await _scalar(conn, f"SELECT 1 FROM reservations WHERE id::text LIKE '%{MARK_SUFFIX}' LIMIT 1"):
        raise SystemExit("Demo data is already there. Run with --clear first if you want to start again.")

    customers = [
        (row[0], row[1])
        for row in (await conn.execute(text("SELECT id, mobile FROM identity_users ORDER BY created_at"))).all()
    ]
    settings_row = await _scalar(conn, "SELECT data FROM reservations_settings WHERE id = 1") or {}
    capacity = (int(settings_row.get("single_capacity", 6)), int(settings_row.get("double_capacity", 1)))
    normal = settings_row.get("normal_prices", {"single": 7_900_000, "double": 10_000_000})
    holiday = settings_row.get("holiday_prices", {"single": 9_400_000, "double": 12_000_000})
    prices = (int(normal["single"]), int(normal["double"]), int(holiday["single"]), int(holiday["double"]))
    entry_ids = [row[0] for row in (await conn.execute(text("SELECT id FROM assistant_knowledge_entries"))).all()]
    preload: dict[tuple[date, time], list[int]] = {}
    for day, session, singles, doubles in (
        await conn.execute(
            text(
                "SELECT business_date, session_time, sum(single_count), sum(double_count) FROM reservations"
                " WHERE status IN ('confirmed', 'attended', 'held') GROUP BY 1, 2"
            )
        )
    ).all():
        preload[(day, session)] = [int(singles), int(doubles)]

    today = now.astimezone(TEHRAN).date()
    start = FiscalCalendar.month_start(
        FiscalCalendar.year_of(today) - 1, 7
    )  # 1 Mehr of last year: about 13 months of history
    start_dt = at(start, time(0))
    ticket_base = int(await _scalar(conn, "SELECT nextval('reservations_ticket_number_seq')")) - 1
    order_base = int(await _scalar(conn, "SELECT nextval('payments_gateway_order_id_seq')")) - 1

    print("generating reservations, payments, texts and events ...")
    data = bookings.generate(
        rng,
        now=now,
        start=start,
        customers=customers,
        capacity=capacity,
        prices=prices,
        target=int(14000 * scale),
        ticket_base=ticket_base,
        order_base=order_base,
        preload=preload,
    )
    sms = data["sms"] + bookings.login_and_bulk_sms(
        rng, now=now, start=start, customers=customers, logins=int(6000 * scale), campaigns=CAMPAIGNS
    )

    print("simulating the books ...")
    accounts = (await conn.execute(text("SELECT id, code, role FROM accounting_accounts"))).all()
    if not accounts:
        raise SystemExit("The chart of accounts is empty; start the API once so it creates the default chart.")
    codes: dict[str, uuid.UUID] = {code: account_id for account_id, code, _ in accounts}
    roles: dict[str, uuid.UUID] = {role: account_id for account_id, _, role in accounts if role}
    new_accounts: list[Row] = []
    for code, name, kind, parent in ledger.EXTRA_ACCOUNTS:
        if code in codes:
            continue
        account_id = new_id(rng)
        codes[code] = account_id
        new_accounts.append(
            {
                "id": account_id,
                "code": code,
                "name": name,
                "type": kind,
                "parent_id": codes[parent],
                "is_group": False,
                "role": None,
                "active": True,
                "is_system": False,
                "created_at": now,
            }
        )
    first_number = {
        int(year): int(last)
        for year, last in (
            await conn.execute(text("SELECT fiscal_year, max(number) FROM accounting_journal_entries GROUP BY 1"))
        ).all()
    }
    books = ledger.build(
        rng, now=now, start=start, sales=data["sales"], roles=roles, codes=codes, first_number=first_number
    )

    print("writing ...")
    counts["accounts"] = await insert_rows(conn, "accounting_accounts", new_accounts)
    counts["reservations"] = await insert_rows(conn, "reservations", data["reservations"])
    counts["payments"] = await insert_rows(conn, "payments_attempts", data["payments"])
    counts["sms"] = await insert_rows(conn, "notifications_sms_messages", sms)
    counts["outbox"] = await insert_rows(conn, "outbox_messages", data["outbox"], jsonb=("payload",))
    counts["vendors"] = await insert_rows(conn, "accounting_vendors", books["vendors"])
    entries = books["entries"]
    counts["journal_entries"] = await insert_rows(
        conn, "accounting_journal_entries", [{k: v for k, v in e.items() if k != "lines"} for e in entries]
    )
    lines = [{"entry_id": e["id"], "line_no": n, **line} for e in entries for n, line in enumerate(e["lines"], start=1)]
    counts["journal_lines"] = await insert_rows(conn, "accounting_journal_lines", lines)
    counts["assets"] = await insert_rows(conn, "accounting_fixed_assets", books["assets"])
    counts["depreciation_runs"] = await insert_rows(conn, "accounting_depreciation_runs", books["runs"])
    counts["budgets"] = await insert_rows(conn, "accounting_budgets", books["budgets"])
    counts["cash_closings"] = await insert_rows(conn, "accounting_cash_closings", books["closings"])
    for counter in books["counters"]:
        await conn.execute(
            text(
                "INSERT INTO accounting_counters (key, value) VALUES (:key, :value)"
                " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            ),
            counter,
        )
    if books.get("lock"):
        await conn.execute(
            text(
                "INSERT INTO accounting_settings (id, data, updated_at) VALUES (1, CAST(:data AS jsonb), now())"
                " ON CONFLICT (id) DO UPDATE SET data = accounting_settings.data || EXCLUDED.data, updated_at = now()"
            ),
            {"data": '{"locked_through": "' + books["lock"][0]["locked_through"].isoformat() + '"}'},
        )

    cache = extras.answer_cache(rng, count=int(300 * scale), now=now, start=start_dt, entry_ids=entry_ids)
    counts["answer_cache"] = await insert_rows(
        conn, "assistant_answer_cache", cache, jsonb=("sources",), vector=("embedding",)
    )
    interactions = extras.assistant_interactions(
        rng,
        count=int(7000 * scale),
        now=now,
        start=start_dt,
        customers=customers,
        entry_ids=entry_ids,
        cache_ids=[c["id"] for c in cache],
    )
    counts["assistant_interactions"] = await insert_rows(
        conn, "assistant_interactions", interactions, jsonb=("source_entry_ids",)
    )
    accounts_rows, ledger_rows = extras.loyalty(rng, now=now, sales=data["sales"])
    counts["loyalty_accounts"] = await insert_rows(conn, "loyalty_accounts", accounts_rows)
    counts["loyalty_ledger"] = await insert_rows(conn, "loyalty_points_ledger", ledger_rows)
    if customers:
        records, inbox = extras.external_bookings(
            rng, count=int(3000 * scale), now=now, start=start_dt, customers=customers
        )
        counts["booking_records"] = await insert_rows(conn, "booking_records", records)
        counts["booking_inbox"] = await insert_rows(conn, "booking_webhook_inbox", inbox)

    last_ticket = max((r["ticket_number"] for r in data["reservations"]), default=ticket_base)
    last_order = max((p["gateway_order_id"] for p in data["payments"]), default=order_base)
    await conn.execute(text("SELECT setval('reservations_ticket_number_seq', :n)"), {"n": last_ticket})
    await conn.execute(text("SELECT setval('payments_gateway_order_id_seq', :n)"), {"n": last_order})
    return counts


async def _run(args: argparse.Namespace) -> int:
    engine = create_async_engine(AppSettings().database_url)
    try:
        async with engine.begin() as conn:
            if args.clear:
                for label, count in (await clear_demo_data(conn)).items():
                    print(f"removed {count:>7}  {label}")
                return 0
            counts = await _seed(
                conn, seed=args.seed, scale=args.scale, now=datetime.now(TEHRAN) - timedelta(seconds=1)
            )
        total = sum(counts.values())
        for label, count in counts.items():
            print(f"added {count:>7}  {label}")
        print(f"total {total} rows")
        return 0
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clear", action="store_true", help="remove the demo data instead of adding it")
    parser.add_argument("--seed", type=int, default=1405, help="random seed (the same seed gives the same data)")
    parser.add_argument("--scale", type=float, default=1.0, help="1.0 is about 120 thousand rows; 0.1 is a quick trial")
    raise SystemExit(asyncio.run(_run(parser.parse_args())))


if __name__ == "__main__":
    main()
