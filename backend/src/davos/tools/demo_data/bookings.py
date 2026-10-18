"""Fake reservations with their payments, confirmation texts and queue events, all consistent with each other."""

from __future__ import annotations

import hashlib
import random
import string
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any

from davos.shared_kernel.domain.jalali_date import JalaliDate
from davos.tools.demo_data.common import MARK, at, new_id, random_clock, session_times, starts_at, weighted
from davos.tools.demo_data.people import full_name, mobile

Row = dict[str, Any]
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
_HOUR_WEIGHT = {15: 0.5, 16: 0.7, 17: 1.0, 18: 1.2, 19: 1.6, 20: 1.8, 21: 1.7, 22: 1.3, 23: 0.8, 0: 0.4}


def _code(rng: random.Random, used: set[str]) -> str:
    while True:
        code = f"{MARK}-" + "".join(rng.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        if code not in used:
            used.add(code)
            return code


def _local_mobile(international: str) -> str:
    digits = "".join(c for c in international if c.isdigit())
    return "0" + digits[-10:]


def generate(
    rng: random.Random,
    *,
    now: datetime,
    start: date,
    customers: list[tuple[uuid.UUID, str]],
    capacity: tuple[int, int],
    prices: tuple[int, int, int, int],
    target: int,
    ticket_base: int,
    order_base: int,
    preload: dict[tuple[date, time], list[int]] | None = None,
) -> dict[str, list[Row]]:
    """``prices`` = normal single, normal double, holiday single, holiday double in Rial."""
    today = now.astimezone(at(start, time(0)).tzinfo).date()
    days = [start + timedelta(days=i) for i in range((today - start).days + 5)]
    span = max(len(days) - 1, 1)
    weights = []
    for index, day in enumerate(days):
        factor = 2.1 if day.weekday() in (3, 4) else 1.35 if day.weekday() == 5 else 1.0
        weights.append((1 + 1.1 * index / span) * factor * (0.5 if day > today else 1.0) * rng.uniform(0.7, 1.3))
    chosen = sorted(rng.choices(days, weights=weights, k=target))
    sessions = session_times()
    session_weights = [_HOUR_WEIGHT[s.hour] for s in sessions]
    load: dict[tuple[date, time], list[int]] = {key: list(value) for key, value in (preload or {}).items()}
    used_codes: set[str] = set()
    used_refs: set[str] = set()
    out: dict[str, list[Row]] = {k: [] for k in ("reservations", "payments", "sms", "outbox", "sales")}
    ticket = ticket_base
    order = order_base

    for day in chosen:
        for _ in range(8):
            session = rng.choices(sessions, weights=session_weights, k=1)[0]
            used = load.setdefault((day, session), [0, 0])
            free_s, free_d = capacity[0] - used[0], capacity[1] - used[1]
            if free_s + free_d > 0:
                break
        else:
            continue
        singles = min(weighted(rng, [(1, 35), (2, 30), (3, 18), (4, 10), (5, 5), (6, 2)]), free_s)
        doubles = 1 if free_d > 0 and (singles == 0 or rng.random() < 0.16) else 0
        if singles + doubles == 0:
            continue
        online = bool(customers) and rng.random() < 0.62
        start_dt = starts_at(day, session)
        past = start_dt < now - timedelta(hours=1)
        holiday = day.weekday() in (3, 4)
        gross = singles * prices[2 if holiday else 0] + doubles * prices[3 if holiday else 1]
        reservation_id = new_id(rng)
        code = _code(rng, used_codes)
        ticket += 1

        if online:
            customer_id, customer_mobile = rng.choice(customers)
            lead = weighted(rng, [(1, 70), (2, 12), (3, 8), (7, 6), (14, 4)])
            created = at(day - timedelta(days=lead), random_clock(rng, 8, 15))
            if created > now - timedelta(minutes=5):
                created = now - timedelta(minutes=rng.randint(10, 200))
            if past:
                status = weighted(rng, [("attended", 82), ("cancelled", 4), ("expired", 14)])
            else:
                status = weighted(rng, [("confirmed", 91), ("cancelled", 4), ("expired", 5)])
            name, contact = full_name(rng), _local_mobile(customer_mobile)
            method = "none"
            amount = gross
        else:
            customer_id = None
            sale_time = (
                start_dt - timedelta(minutes=rng.randint(5, 120))
                if not day > today
                else now - timedelta(hours=rng.randint(1, 40))
            )
            created = min(sale_time, now - timedelta(minutes=3))
            status = (
                weighted(rng, [("attended", 92), ("cancelled", 8)])
                if past
                else weighted(rng, [("confirmed", 94), ("cancelled", 6)])
            )
            name, contact = full_name(rng), mobile(rng)
            method = weighted(rng, [("cash", 55), ("card", 33), ("transfer", 8), ("none", 4)])
            amount = 0 if method == "none" else (gross * 9 // 10 // 100_000 * 100_000 if rng.random() < 0.05 else gross)

        if status != "expired":
            used[0] += singles
            used[1] += doubles
        confirmed_at = (
            None if status == "expired" else (created + timedelta(minutes=rng.randint(2, 7)) if online else created)
        )
        updated = confirmed_at or created + timedelta(minutes=20)
        cancel_reason = ""
        if status == "attended":
            updated = start_dt + timedelta(minutes=20)
        elif status == "cancelled":
            updated = min(
                (confirmed_at or created) + timedelta(hours=rng.randint(1, 20)), now - timedelta(minutes=1), start_dt
            )
            updated = max(updated, (confirmed_at or created) + timedelta(minutes=1))
            cancel_reason = rng.choice(
                ["انصراف مشتری", "تغییر برنامه", "درخواست مشتری برای لغو", "پرداخت توسط بانک برگشت خورد"]
            )
        payment_ref = None
        if online and status != "expired":
            while True:
                payment_ref = str(rng.randint(10**8, 10**9 - 1))
                if payment_ref not in used_refs:
                    used_refs.add(payment_ref)
                    break
        out["reservations"].append(
            {
                "id": reservation_id,
                "code": code,
                "customer_id": customer_id,
                "business_date": day,
                "session_time": session,
                "starts_at": start_dt,
                "single_count": singles,
                "double_count": doubles,
                "amount_irr": amount,
                "status": status,
                "source": "online" if online else "staff",
                "contact_name": name,
                "contact_mobile": contact,
                "created_at": created,
                "updated_at": updated,
                "hold_expires_at": created + timedelta(minutes=20) if online else None,
                "confirmed_at": confirmed_at,
                "payment_ref": payment_ref,
                "confirmed_late": online and status != "expired" and rng.random() < 0.01,
                "note": ""
                if online or rng.random() < 0.7
                else rng.choice(["تولد", "گروه شرکتی", "همراه با کودک", "دوستانه"]),
                "cancel_reason": cancel_reason,
                "ticket_number": ticket,
                "payment_method": method,
            }
        )
        jalali = JalaliDate.from_gregorian(day)
        confirm_text = f"تایید رزرو {code} - {jalali.numeric()} ساعت {session.strftime('%H:%M')}".translate(
            _DIGITS
        ) + f"\nشماره بلیت: {ticket}".translate(_DIGITS)

        if online:
            gateway = "zarinpal" if rng.random() < 0.7 else "mellat"
            attempts: list[tuple[str, datetime, str | None]] = []
            if status == "expired":
                if rng.random() < 0.7:
                    attempts.append(
                        (weighted(rng, [("expired", 60), ("failed", 40)]), created + timedelta(seconds=15), None)
                    )
            else:
                if rng.random() < 0.14:
                    attempts.append(
                        (
                            "failed",
                            created + timedelta(seconds=20),
                            rng.choice(["user_cancelled", "insufficient_funds", "bank_declined"]),
                        )
                    )
                attempts.append(("paid", created + timedelta(seconds=rng.randint(40, 150)), None))
            for attempt_status, attempt_at, reason in attempts:
                order += 1
                paid = attempt_status == "paid"
                authority = (
                    ("A" + "".join(rng.choice(string.digits) for _ in range(35)))
                    if gateway == "zarinpal"
                    else "".join(rng.choice("0123456789ABCDEF") for _ in range(16))
                )
                out["payments"].append(
                    {
                        "id": new_id(rng),
                        "order_ref": f"reservation:{reservation_id}",
                        "customer_id": customer_id,
                        "amount_irr": amount,
                        "status": attempt_status,
                        "authority": authority,
                        "reference_id": payment_ref if paid else None,
                        "failure_reason": reason,
                        "created_at": attempt_at - timedelta(seconds=10),
                        "updated_at": confirmed_at if paid and confirmed_at else attempt_at,
                        "expires_at": attempt_at + timedelta(minutes=30),
                        "gateway": gateway,
                        "gateway_order_id": order,
                        "provider_reference": (
                            "".join(rng.choice(string.digits) for _ in range(12))
                            if paid and gateway == "mellat"
                            else None
                        ),
                        "settled_at": (confirmed_at + timedelta(seconds=5)) if paid and confirmed_at else None,
                    }
                )
                if paid and confirmed_at:
                    out["outbox"].append(
                        _event(
                            rng,
                            "payments.PaymentSucceeded",
                            confirmed_at,
                            {
                                "payment_id": str(out["payments"][-1]["id"]),
                                "order_ref": f"reservation:{reservation_id}",
                                "amount_irr": amount,
                                "reference_id": payment_ref,
                            },
                        )
                    )
            if confirmed_at:
                out["sms"].append(_sms(rng, "transactional", contact, confirm_text, confirmed_at))
        if confirmed_at and (online or method != "none"):
            out["outbox"].append(
                _event(
                    rng,
                    "reservations.ReservationConfirmed",
                    confirmed_at,
                    {
                        "reservation_id": str(reservation_id),
                        "code": code,
                        "amount_irr": amount,
                        "source": "online" if online else "staff",
                    },
                )
            )
        if status == "cancelled":
            out["outbox"].append(
                _event(
                    rng,
                    "reservations.ReservationCancelled",
                    updated,
                    {"reservation_id": str(reservation_id), "code": code, "was_paid": online, "reason": cancel_reason},
                )
            )

        if confirmed_at and amount > 0 and (online or method != "none"):
            out["sales"].append(
                {
                    "id": str(reservation_id),
                    "ticket": ticket,
                    "online": online,
                    "method": method if not online else None,
                    "amount": amount,
                    "at": confirmed_at,
                    "session_day": day,
                    "refunded": status == "cancelled",
                    "refund_at": updated if status == "cancelled" else None,
                    "gateway": gateway if online else None,
                    "customer_id": customer_id,
                    "status": status,
                }
            )
    return out


def _event(rng: random.Random, name: str, when: datetime, payload: dict[str, Any]) -> Row:
    return {
        "event_id": new_id(rng),
        "event_name": name,
        "payload": {**payload, "demo": True},
        "occurred_at": when,
        "created_at": when,
        "available_at": when,
        "published_at": when + timedelta(seconds=2),
        "attempts": 1,
        "last_error": None,
        "dead_lettered_at": None,
    }


def _sms(
    rng: random.Random,
    kind: str,
    recipient: str,
    body: str,
    when: datetime,
    *,
    batch: uuid.UUID | None = None,
    by: str = "",
) -> Row:
    status = weighted(rng, [("delivered", 90), ("sent", 5), ("failed", 3), ("blocked", 1), ("unknown", 1)])
    return {
        "id": new_id(rng),
        "kind": kind,
        "recipient": recipient,
        "body": body,
        "status": status,
        "provider_message_id": "DM" + str(rng.randint(10**9, 10**10 - 1)),
        "batch_id": batch,
        "sent_by": by,
        "error": "خطای اپراتور" if status == "failed" else "",
        "created_at": when,
        "updated_at": when + timedelta(seconds=rng.randint(2, 40)),
    }


def login_and_bulk_sms(
    rng: random.Random,
    *,
    now: datetime,
    start: date,
    customers: list[tuple[uuid.UUID, str]],
    logins: int,
    campaigns: list[str],
) -> list[Row]:
    rows: list[Row] = []
    span = int((now - at(start, time(0))).total_seconds())
    for _ in range(logins):
        when = at(start, time(0)) + timedelta(seconds=rng.randint(0, span))
        code = "".join(rng.choice(string.digits) for _ in range(6)).translate(_DIGITS)
        recipient = _local_mobile(rng.choice(customers)[1]) if customers else mobile(rng)
        rows.append(_sms(rng, "transactional", recipient, f"کد ورود داووس کارتینگ: {code}", when))
    for index in range(26):
        batch = new_id(rng)
        when = at(start, time(12)) + timedelta(
            days=int(index * ((now - at(start, time(0))).days / 26)), minutes=rng.randint(0, 300)
        )
        text = campaigns[index % len(campaigns)]
        for _ in range(rng.randint(150, 600)):
            rows.append(_sms(rng, "bulk", mobile(rng), text, when, batch=batch, by="owner"))
    return rows


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
