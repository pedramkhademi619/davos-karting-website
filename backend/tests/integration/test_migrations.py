import os
import subprocess
import sys

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.conftest import BACKEND_DIR, DATABASE_URL

pytestmark = pytest.mark.integration

NOW = "2026-01-01T12:00:00+00:00"


async def test_expected_tables_exist(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        rows = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = {r[0] for r in rows}
    assert {"identity_users", "identity_otp_challenges", "identity_sessions", "outbox_messages"} <= tables
    assert "alembic_version" in tables


async def test_database_rejects_malformed_mobile_numbers(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(
                    "INSERT INTO identity_users (id, mobile, status, created_at) "
                    "VALUES (gen_random_uuid(), '09123456789', 'active', now())"
                )
            )


async def test_database_enforces_unique_mobile_and_valid_status(engine: AsyncEngine) -> None:
    insert = text(
        "INSERT INTO identity_users (id, mobile, status, created_at) "
        "VALUES (gen_random_uuid(), :mobile, :status, now())"
    )
    async with engine.begin() as conn:
        await conn.execute(insert, {"mobile": "+989123456789", "status": "active"})
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(insert, {"mobile": "+989123456789", "status": "active"})
    async with engine.connect() as conn:
        with pytest.raises(IntegrityError):
            await conn.execute(insert, {"mobile": "+989123456780", "status": "superuser"})


async def test_timestamps_are_timestamptz(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text(
                "SELECT table_name, column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = 'public' AND column_name LIKE '%\\_at' ESCAPE '\\'"
            )
        )
        offenders = [(t, c) for t, c, d in rows if d != "timestamp with time zone"]
    assert offenders == []


def _alembic(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "MIGRATION_DATABASE_URL": DATABASE_URL}
    return subprocess.run(  # noqa: S603 - fixed arguments, test-only
        [sys.executable, "-m", "alembic", *args], cwd=BACKEND_DIR, env=env, capture_output=True, text=True, check=False
    )


def test_models_and_migrations_have_not_drifted() -> None:
    """Fails when someone changes an ORM model without writing the migration (or the reverse)."""
    result = _alembic("check")
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_migration_can_be_reversed_and_reapplied() -> None:
    """downgrade to empty, then upgrade again: proves each migration's downgrade() actually works."""
    down = _alembic("downgrade", "base")
    assert down.returncode == 0, down.stderr
    up = _alembic("upgrade", "head")
    assert up.returncode == 0, up.stderr
