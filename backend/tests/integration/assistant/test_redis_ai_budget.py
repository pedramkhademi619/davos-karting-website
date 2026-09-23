from __future__ import annotations

import asyncio

import pytest
from redis.asyncio import Redis

from davos.modules.assistant.adapters.budget.redis_ai_budget import RedisAiBudget
from tests.fakes.fixed_clock import FixedClock

pytestmark = pytest.mark.integration


async def test_concurrent_reservations_never_exceed_the_daily_limit(redis_client: Redis, clock: FixedClock) -> None:
    replicas = [RedisAiBudget(redis_client, daily_limit=100, clock=clock) for _ in range(4)]
    results = await asyncio.gather(*(replicas[i % 4].try_reserve(10) for i in range(40)))
    assert sum(results) == 10  # exactly 100 tokens' worth granted across all replicas
    assert int(await redis_client.get(f"ai:budget:tokens:{clock.now().date().isoformat()}")) == 100


async def test_settle_replaces_the_reservation_with_actual_usage(redis_client: Redis, clock: FixedClock) -> None:
    budget = RedisAiBudget(redis_client, daily_limit=1000, clock=clock)
    assert await budget.try_reserve(500)
    await budget.settle(reserved=500, actual=120)
    assert int(await redis_client.get(f"ai:budget:tokens:{clock.now().date().isoformat()}")) == 120


async def test_release_returns_tokens_and_a_new_day_starts_fresh(redis_client: Redis, clock: FixedClock) -> None:
    budget = RedisAiBudget(redis_client, daily_limit=100, clock=clock)
    assert await budget.try_reserve(100)
    assert not await budget.try_reserve(1)
    await budget.release(100)
    assert await budget.try_reserve(100)
    clock.advance(days=1)
    assert await budget.try_reserve(100)  # new day, new counter


async def test_counter_expires_so_old_days_do_not_accumulate(redis_client: Redis, clock: FixedClock) -> None:
    budget = RedisAiBudget(redis_client, daily_limit=100, clock=clock)
    await budget.try_reserve(1)
    ttl = await redis_client.ttl(f"ai:budget:tokens:{clock.now().date().isoformat()}")
    assert 0 < ttl <= 172_800
