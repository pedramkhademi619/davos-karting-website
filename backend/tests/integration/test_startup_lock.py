"""Several API worker processes start together: exactly one of them does the start-up work."""

from __future__ import annotations

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from davos.platform.persistence.startup_lock import StartupLock

pytestmark = pytest.mark.integration


async def test_only_one_of_many_simultaneous_starts_gets_the_lock(engine: AsyncEngine) -> None:
    release = asyncio.Event()
    all_tried = asyncio.Event()
    got: list[bool] = []

    async def start() -> None:
        async with StartupLock(engine, "test-startup").acquired() as mine:
            got.append(mine)
            if len(got) == 4:
                all_tried.set()
            await release.wait()  # hold the lock while the others try

    tasks = [asyncio.create_task(start()) for _ in range(4)]
    await asyncio.wait_for(all_tried.wait(), timeout=10)
    release.set()
    await asyncio.gather(*tasks)
    assert got.count(True) == 1

    async with StartupLock(engine, "test-startup").acquired() as mine:
        assert mine  # released afterwards
