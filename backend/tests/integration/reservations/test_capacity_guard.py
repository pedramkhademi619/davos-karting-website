"""The database backstop (migration 0011) against overselling a session with online reservations.

These are independent of the application's advisory-lock path: they insert rows straight into the table to prove the
trigger holds even when a caller bypasses the use case. Confirmed rows are used for the capacity assertions so the
checks do not depend on wall-clock time; one case covers that an expired hold is not counted.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration

_INSERT = text(
    "INSERT INTO reservations "
    "(id, code, customer_id, business_date, session_time, starts_at, single_count, double_count, amount_irr, "
    " status, source, created_at, updated_at, hold_expires_at) "
    "VALUES (gen_random_uuid(), :code, :customer, :day, :t, :starts, :s, :d, 100, "
    " :status, :source, now(), now(), :expires)"
)


async def _insert(engine: AsyncEngine, **kw: object) -> None:
    params = {
        "code": uuid.uuid4().hex[:12],
        "customer": uuid.uuid4() if kw.get("source", "online") == "online" else None,
        "day": "2030-05-01",
        "t": "18:00",
        "starts": "2030-05-01 18:00:00+03:30",
        "s": 0,
        "d": 0,
        "status": "confirmed",
        "source": "online",
        "expires": None,
        **kw,
    }
    async with engine.begin() as conn:
        await conn.execute(_INSERT, params)


async def _set_capacity(engine: AsyncEngine, singles: int, doubles: int) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO reservations_settings (id, data, updated_at) "
                "VALUES (1, :data, now()) ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data"
            ),
            {"data": f'{{"single_capacity": {singles}, "double_capacity": {doubles}}}'},
        )


async def test_online_bookings_cannot_exceed_single_capacity(engine: AsyncEngine) -> None:
    await _set_capacity(engine, 6, 1)
    await _insert(engine, s=6)  # fills the six single-seaters
    with pytest.raises(IntegrityError, match="session_oversold"):
        await _insert(engine, s=1)  # the seventh single-seater must be refused by the database


async def test_online_bookings_cannot_exceed_double_capacity(engine: AsyncEngine) -> None:
    await _set_capacity(engine, 6, 1)
    await _insert(engine, d=1)
    with pytest.raises(IntegrityError, match="session_oversold"):
        await _insert(engine, d=1)


async def test_staff_may_overbook_a_full_session(engine: AsyncEngine) -> None:
    await _set_capacity(engine, 6, 1)
    await _insert(engine, s=6)
    await _insert(engine, s=10, source="staff", customer=None)  # walk-ins: deliberately allowed


async def test_an_expired_hold_frees_the_seats(engine: AsyncEngine) -> None:
    await _set_capacity(engine, 6, 1)
    # an online hold whose expiry is well in the past, so the trigger must not count it
    await _insert(engine, s=6, status="held", expires="2020-01-01 00:00:00+00:00")
    await _insert(engine, s=6)  # the expired hold does not count, so a fresh full booking is allowed


async def test_a_live_hold_still_blocks_a_new_booking(engine: AsyncEngine) -> None:
    await _set_capacity(engine, 6, 1)
    await _insert(engine, s=6, status="held", expires="2099-01-01 00:00:00+00:00")  # far-future hold occupies the seats
    with pytest.raises(IntegrityError, match="session_oversold"):
        await _insert(engine, s=1)


async def test_capacity_defaults_apply_when_no_settings_row_exists(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM reservations_settings"))
    await _insert(engine, s=6)  # default single capacity is 6
    with pytest.raises(IntegrityError, match="session_oversold"):
        await _insert(engine, s=1)
