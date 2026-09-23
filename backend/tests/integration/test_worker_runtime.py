"""Regression: consecutive Celery tasks each run in a fresh event loop.

The first version shared one container across tasks and every task after the first failed with
"attached to a different loop" (found by running the compose stack).
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings
from davos.worker.worker_runtime import WorkerRuntime

pytestmark = pytest.mark.integration


async def _touch_every_async_dependency(container: ApplicationContainer) -> str:
    async with container.engine.connect() as connection:
        await connection.execute(text("SELECT 1"))
    assert container.redis is not None
    await container.redis.ping()  # type: ignore[misc]
    return "ok"


def test_consecutive_jobs_each_get_working_async_resources(test_settings: AppSettings) -> None:
    # Synchronous test on purpose: WorkerRuntime.run owns its event loop, exactly like a Celery task.
    results = [WorkerRuntime.run(_touch_every_async_dependency, test_settings) for _ in range(3)]
    assert results == ["ok", "ok", "ok"]


def test_the_container_is_closed_after_each_job(test_settings: AppSettings) -> None:
    seen: list[ApplicationContainer] = []

    async def job(container: ApplicationContainer) -> None:
        seen.append(container)

    WorkerRuntime.run(job, test_settings)
    WorkerRuntime.run(job, test_settings)
    assert seen[0] is not seen[1]
