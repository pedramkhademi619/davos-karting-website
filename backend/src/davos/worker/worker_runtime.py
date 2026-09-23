from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from davos.composition.application_container import ApplicationContainer
from davos.platform.settings.app_settings import AppSettings

T = TypeVar("T")


class WorkerRuntime:
    """Runs one async job per Celery task.

    Celery tasks are synchronous, so every task gets its own event loop via ``asyncio.run``. Async
    resources (database engine, Redis, HTTP client) are bound to the loop that created them, so the
    container is built inside the loop and closed before it ends; sharing one across tasks fails with
    "attached to a different loop".
    """

    @staticmethod
    def run(job: Callable[[ApplicationContainer], Awaitable[T]], settings: AppSettings | None = None) -> T:
        async def main() -> T:
            container = ApplicationContainer.build(settings or AppSettings())
            try:
                return await job(container)
            finally:
                await container.aclose()

        return asyncio.run(main())
