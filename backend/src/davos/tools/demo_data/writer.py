"""Bulk writing and clearing for the demo data (plain SQL, a few thousand rows per statement)."""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from davos.tools.demo_data.common import MARK_SUFFIX, chunks

Row = dict[str, Any]
_CHUNK = 2000


async def insert_rows(
    conn: AsyncConnection, table: str, rows: Sequence[Row], *, jsonb: Sequence[str] = (), vector: Sequence[str] = ()
) -> int:
    if not rows:
        return 0
    columns = list(rows[0])
    values = []
    for column in columns:
        if column in jsonb:
            values.append(f"CAST(:{column} AS jsonb)")
        elif column in vector:
            values.append(f"CAST(:{column} AS vector)")
        else:
            values.append(f":{column}")
    statement = text(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)})")
    for part in chunks(list(rows), _CHUNK):
        prepared = [{k: (json.dumps(v) if k in jsonb else v) for k, v in row.items()} for row in part]
        await conn.execute(statement, prepared)
    return len(rows)


_MARKED = f"id::text LIKE '%{MARK_SUFFIX}'"


async def clear_demo_data(conn: AsyncConnection) -> dict[str, int]:
    """Removes everything the seeder created (it is recognised by the marker every demo uuid carries)."""
    removed: dict[str, int] = {}

    async def delete(label: str, sql: str) -> None:
        result = await conn.execute(text(sql))
        removed[label] = result.rowcount or 0

    for table in ("accounting_journal_lines", "accounting_journal_entries", "loyalty_points_ledger"):
        await conn.execute(text(f"ALTER TABLE {table} DISABLE TRIGGER USER"))
    try:
        entries = f"SELECT id FROM accounting_journal_entries WHERE {_MARKED}"
        await delete("cash_closings", f"DELETE FROM accounting_cash_closings WHERE {_MARKED}")
        await delete("depreciation_runs", f"DELETE FROM accounting_depreciation_runs WHERE entry_id IN ({entries})")
        await delete("journal_lines", f"DELETE FROM accounting_journal_lines WHERE entry_id IN ({entries})")
        closing = (
            await conn.execute(
                text(f"SELECT count(*) FROM accounting_journal_entries WHERE {_MARKED} AND source = 'closing'")
            )
        ).scalar_one()
        await delete("journal_entries", f"DELETE FROM accounting_journal_entries WHERE {_MARKED}")
        await delete("assets", f"DELETE FROM accounting_fixed_assets WHERE {_MARKED}")
        await delete("vendors", f"DELETE FROM accounting_vendors WHERE {_MARKED}")
        await delete("budgets", "DELETE FROM accounting_budgets")
        await conn.execute(
            text(
                "DELETE FROM accounting_counters c WHERE NOT EXISTS (SELECT 1 FROM accounting_journal_entries e"
                " WHERE 'journal:' || e.fiscal_year = c.key)"
            )
        )
        await conn.execute(
            text(
                "UPDATE accounting_counters c SET value = (SELECT COALESCE(MAX(number), 0)"
                " FROM accounting_journal_entries e"
                " WHERE 'journal:' || e.fiscal_year = c.key)"
            )
        )
        if closing:
            await conn.execute(text("UPDATE accounting_settings SET data = data - 'locked_through' WHERE id = 1"))
        await delete("loyalty_ledger", f"DELETE FROM loyalty_points_ledger WHERE {_MARKED}")
        await delete(
            "loyalty_accounts",
            "DELETE FROM loyalty_accounts a WHERE NOT EXISTS"
            " (SELECT 1 FROM loyalty_points_ledger l WHERE l.customer_id = a.customer_id)",
        )
    finally:
        for table in ("accounting_journal_lines", "accounting_journal_entries", "loyalty_points_ledger"):
            await conn.execute(text(f"ALTER TABLE {table} ENABLE TRIGGER USER"))
    reservations = f"SELECT 'reservation:' || id::text FROM reservations WHERE {_MARKED}"
    await delete("payments", f"DELETE FROM payments_attempts WHERE order_ref IN ({reservations})")
    await delete("sms", "DELETE FROM notifications_sms_messages WHERE provider_message_id LIKE 'DM%'")
    await delete("outbox", "DELETE FROM outbox_messages WHERE payload ->> 'demo' = 'true'")
    await delete("reservations", f"DELETE FROM reservations WHERE {_MARKED}")
    await delete("assistant_interactions", f"DELETE FROM assistant_interactions WHERE {_MARKED}")
    await delete("answer_cache", f"DELETE FROM assistant_answer_cache WHERE {_MARKED}")
    await delete("booking_records", f"DELETE FROM booking_records WHERE {_MARKED}")
    await delete("booking_inbox", "DELETE FROM booking_webhook_inbox WHERE event_id LIKE 'demo-evt-%'")
    return removed
