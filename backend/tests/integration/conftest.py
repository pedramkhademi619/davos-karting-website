"""Integration fixtures: real PostgreSQL (schema built by Alembic migrations) and real Redis.

Defaults match ``docker run`` commands in docs/TESTING.md; override with TEST_DATABASE_URL and
TEST_REDIS_URL in CI. There is deliberately no SQLite fallback: PostgreSQL-specific behaviour
(row locks, partial indexes, ON CONFLICT, pg_trgm) is part of what is being tested.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from davos.composition.application_container import ApplicationContainer
from davos.modules.assistant.adapters.budget.in_memory_ai_budget import InMemoryAiBudget
from davos.modules.notifications.adapters.sms.recording_sms_gateway import RecordingSmsGateway
from davos.platform.persistence.base import Base
from davos.platform.persistence.model_registry import register_all_models
from davos.platform.rate_limiting.in_memory_rate_limiter import InMemoryRateLimiter
from davos.platform.settings.app_environment import AppEnvironment
from davos.platform.settings.app_settings import AppSettings
from tests.fakes.fixed_clock import FixedClock
from tests.fakes.fixed_order_quotes import FixedOrderQuotes
from tests.fakes.scripted_ai_chat import ScriptedAiChat
from tests.fakes.scripted_payment_gateway import ScriptedPaymentGateway
from tests.support.booking_webhooks import SECRET as BOOKING_SECRET

DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:54329/davos_test")
REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:63799/0")
BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic(*args: str) -> None:
    env = {**os.environ, "MIGRATION_DATABASE_URL": DATABASE_URL}
    subprocess.run(  # noqa: S603 - fixed arguments, test-only
        [sys.executable, "-m", "alembic", *args], cwd=BACKEND_DIR, env=env, check=True, capture_output=True
    )


async def _reset_schema() -> None:
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    except OSError as exc:  # pragma: no cover
        pytest.exit(f"PostgreSQL is not reachable at {DATABASE_URL}: {exc}", returncode=2)
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> None:
    """Build the schema exclusively through Alembic, exactly as production does."""
    asyncio.run(_reset_schema())
    _alembic("upgrade", "head")


@pytest.fixture
def test_settings() -> AppSettings:
    return AppSettings(
        app_env=AppEnvironment.TEST,
        database_url=DATABASE_URL,
        redis_url=REDIS_URL,
        cookie_secure=False,
        payments_enabled=True,
        booking_integration_enabled=True,
        booking_webhook_secret=BOOKING_SECRET,
    )


@pytest.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    register_all_models()
    engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        tables = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield engine
    await engine.dispose()


@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    client = Redis.from_url(REDIS_URL, decode_responses=True)
    await client.flushdb()
    yield client
    await client.aclose()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def sms_gateway() -> RecordingSmsGateway:
    return RecordingSmsGateway()


@pytest.fixture
def ai_chat() -> ScriptedAiChat:
    return ScriptedAiChat("پاسخ نمونه [1]")


@pytest.fixture
def gateway() -> ScriptedPaymentGateway:
    return ScriptedPaymentGateway()


@pytest.fixture
def quotes() -> FixedOrderQuotes:
    return FixedOrderQuotes()


@pytest.fixture
def container(
    test_settings: AppSettings,
    engine: AsyncEngine,
    clock: FixedClock,
    sms_gateway: RecordingSmsGateway,
    ai_chat: ScriptedAiChat,
    gateway: ScriptedPaymentGateway,
    quotes: FixedOrderQuotes,
) -> ApplicationContainer:
    return ApplicationContainer(
        settings=test_settings,
        engine=engine,
        redis=None,
        clock=clock,
        rate_limiter=InMemoryRateLimiter(clock),
        sms_gateway=sms_gateway,
        ai_chat=ai_chat,
        ai_budget=InMemoryAiBudget(daily_limit=1_000_000, clock=clock),
        payment_gateway=gateway,
        order_quotes=quotes,
    )
