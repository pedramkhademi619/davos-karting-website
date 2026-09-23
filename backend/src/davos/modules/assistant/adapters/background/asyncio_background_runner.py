from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any

from davos.modules.assistant.application.ports.background_runner_port import BackgroundRunnerPort

logger = logging.getLogger(__name__)


class AsyncioBackgroundRunner(BackgroundRunnerPort):
    """Runs work on the event loop after the request has been answered, and lets shutdown wait for what is left."""

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[None]] = set()

    def run(self, work: Coroutine[Any, Any, None], *, name: str) -> None:
        task = asyncio.create_task(self._guarded(work, name), name=name)
        self._tasks.add(task)  # a strong reference: the event loop keeps only weak ones, so a task could vanish mid-way
        task.add_done_callback(self._tasks.discard)

    async def drain(self, timeout_seconds: float = 5.0) -> None:
        pending = list(self._tasks)
        if pending:
            await asyncio.wait(pending, timeout=timeout_seconds)

    @staticmethod
    async def _guarded(work: Coroutine[Any, Any, None], name: str) -> None:
        try:
            await work
        except Exception as exc:
            logger.warning("background job %s failed: %s", name, type(exc).__name__)
