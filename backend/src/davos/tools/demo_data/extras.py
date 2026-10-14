"""Fake assistant conversations, cached answers, loyalty points and external-system bookings."""

from __future__ import annotations

import json
import math
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Any

from davos.tools.demo_data.bookings import fingerprint
from davos.tools.demo_data.common import new_id, weighted
from davos.tools.demo_data.people import OUTCOMES, QUESTIONS

Row = dict[str, Any]


def assistant_interactions(
    rng: random.Random,
    *,
    count: int,
    now: datetime,
    start: datetime,
    customers: list[tuple[uuid.UUID, str]],
    entry_ids: list[uuid.UUID],
    cache_ids: list[uuid.UUID],
) -> list[Row]:
    rows: list[Row] = []
    span = int((now - start).total_seconds())
    for _ in range(count):
        when = start + timedelta(seconds=rng.randint(0, span))
        outcome = weighted(rng, [(name, float(w)) for name, w in OUTCOMES])
        question, answer = rng.choice(QUESTIONS)
        stored = rng.random() < 0.3
        cached = outcome == "served_from_cache"
        rows.append(
            {
                "id": new_id(rng),
                "occurred_at": when,
                "outcome": outcome,
                "prompt_tokens": 0
                if outcome in ("quick_answer", "small_talk", "served_from_cache")
                else rng.randint(900, 2600),
                "completion_tokens": 0
                if outcome in ("quick_answer", "small_talk", "served_from_cache")
                else rng.randint(40, 260),
                "source_entry_ids": [str(rng.choice(entry_ids))]
                if entry_ids and outcome in ("answered", "quick_answer")
                else [],
                "retention_until": when + timedelta(days=90),
                "conversation_id": new_id(rng),
                "user_id": rng.choice(customers)[0] if customers and rng.random() < 0.4 else None,
                "question_text": question if stored else None,
                "answer_text": answer if stored else None,
                "helpful": rng.choice([True, True, True, False]) if rng.random() < 0.25 else None,
                "cache_entry_id": rng.choice(cache_ids) if cached and cache_ids else None,
                "served_from_cache": cached,
            }
        )
    return rows


def _unit_vector(rng: random.Random, size: int = 384) -> str:
    values = [rng.gauss(0, 1) for _ in range(size)]
    norm = math.sqrt(sum(v * v for v in values)) or 1.0
    return "[" + ",".join(f"{v / norm:.6f}" for v in values) + "]"


def answer_cache(
    rng: random.Random, *, count: int, now: datetime, start: datetime, entry_ids: list[uuid.UUID]
) -> list[Row]:
    rows: list[Row] = []
    span = int((now - start).total_seconds())
    fillers = ["لطفا", "ببخشید", "میشه بگید", "سلام", "یه سوال داشتم", ""]
    for index in range(count):
        question, answer = QUESTIONS[index % len(QUESTIONS)]
        text = (
            f"{rng.choice(fillers)} {question}".strip() + (" " * 0) + (f" ({index})" if index >= len(QUESTIONS) else "")
        )
        created = start + timedelta(seconds=rng.randint(0, span))
        rows.append(
            {
                "id": new_id(rng),
                "original_query": text,
                "resolved_query": question,
                "signature": "",
                "embedding": _unit_vector(rng),
                "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
                "fingerprint": fingerprint(text),
                "response": answer,
                "sources": [{"entry_id": str(rng.choice(entry_ids)), "title": "منبع"}] if entry_ids else [],
                "hit_count": rng.randint(0, 120),
                "is_active": rng.random() > 0.05,
                "created_at": created,
                "last_used_at": min(now, created + timedelta(days=rng.randint(0, 90))),
            }
        )
    return rows


def loyalty(rng: random.Random, *, now: datetime, sales: list[Row]) -> tuple[list[Row], list[Row]]:
    accounts: dict[uuid.UUID, datetime] = {}
    ledger: list[Row] = []
    earned: dict[uuid.UUID, int] = {}
    for sale in sales:
        customer = sale.get("customer_id")
        if customer is None or sale["status"] != "attended":
            continue
        points = max(1, sale["amount"] // 100_000)
        when = sale["at"] + timedelta(hours=2)
        if when > now:
            continue
        accounts.setdefault(customer, when)
        expires = when + timedelta(days=365)
        ledger.append(
            {
                "id": new_id(rng),
                "customer_id": customer,
                "delta": points,
                "kind": "earn",
                "source_ref": f"reservation:{sale['id']}",
                "reason": f"امتیاز بلیت {sale['ticket']}",
                "reverses_kind": None,
                "created_at": when,
                "expires_at": expires,
            }
        )
        earned[customer] = earned.get(customer, 0) + points
        if expires < now:
            ledger.append(
                {
                    "id": new_id(rng),
                    "customer_id": customer,
                    "delta": -points,
                    "kind": "expire",
                    "source_ref": f"expire:{sale['id']}",
                    "reason": "انقضای امتیاز",
                    "reverses_kind": "earn",
                    "created_at": expires,
                    "expires_at": None,
                }
            )
            earned[customer] -= points
    for customer, balance in earned.items():
        if balance >= 150 and rng.random() < 0.35:
            take = rng.randint(50, min(balance, 400))
            ledger.append(
                {
                    "id": new_id(rng),
                    "customer_id": customer,
                    "delta": -take,
                    "kind": "spend",
                    "source_ref": f"redeem:{rng.getrandbits(40):x}",
                    "reason": "استفاده از امتیاز در رزرو",
                    "reverses_kind": None,
                    "created_at": now - timedelta(days=rng.randint(1, 120)),
                    "expires_at": None,
                }
            )
        if rng.random() < 0.05:
            ledger.append(
                {
                    "id": new_id(rng),
                    "customer_id": customer,
                    "delta": rng.choice([-20, 30, 50]),
                    "kind": "adjust",
                    "source_ref": f"adjust:{rng.getrandbits(40):x}",
                    "reason": "اصلاح دستی توسط پشتیبانی",
                    "reverses_kind": None,
                    "created_at": now - timedelta(days=rng.randint(1, 200)),
                    "expires_at": None,
                }
            )
    return [{"customer_id": c, "created_at": t} for c, t in accounts.items()], ledger


def external_bookings(
    rng: random.Random, *, count: int, now: datetime, start: datetime, customers: list[tuple[uuid.UUID, str]]
) -> tuple[list[Row], list[Row]]:
    records: list[Row] = []
    inbox: list[Row] = []
    span = int((now - start).total_seconds())
    for _ in range(count):
        when = start + timedelta(seconds=rng.randint(0, span))
        external = "EXT-" + "".join(rng.choice(string.hexdigits.upper()[:16]) for _ in range(8))
        status = weighted(
            rng,
            [("confirmed", 30), ("attended", 45), ("cancelled", 10), ("no_show", 8), ("pending", 4), ("refunded", 3)],
        )
        event_id = f"demo-evt-{rng.getrandbits(48):012x}"
        records.append(
            {
                "id": new_id(rng),
                "external_booking_id": external,
                "user_id": rng.choice(customers)[0],
                "status": status,
                "amount_irr": rng.randint(70, 250) * 100_000,
                "session_time": when + timedelta(days=rng.randint(0, 6)),
                "last_updated_at": when,
                "last_event_id": event_id,
                "created_at": when,
            }
        )
        outcome = weighted(rng, [("processed", 93), ("failed", 5), ("received", 2)])
        inbox.append(
            {
                "event_id": event_id,
                "body": json.dumps({"booking_id": external, "status": status}),
                "status": outcome,
                "attempts": 1 if outcome != "failed" else 3,
                "last_error_code": "invalid_signature" if outcome == "failed" else None,
                "received_at": when,
                "processed_at": when + timedelta(seconds=2) if outcome == "processed" else None,
            }
        )
    return records, inbox
