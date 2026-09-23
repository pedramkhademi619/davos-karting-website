from __future__ import annotations

from collections.abc import Coroutine
from typing import Any

from davos.modules.assistant.application.ports.background_runner_port import BackgroundRunnerPort


class ImmediateBackgroundRunner(BackgroundRunnerPort):
    """Keeps the work instead of scheduling it; ``settle`` runs it, so a test decides when "later" happens."""

    def __init__(self) -> None:
        self._pending: list[Coroutine[Any, Any, None]] = []
        self.names: list[str] = []

    def run(self, work: Coroutine[Any, Any, None], *, name: str) -> None:
        self._pending.append(work)
        self.names.append(name)

    async def settle(self) -> None:
        pending, self._pending = self._pending, []
        for work in pending:
            await work

    def __del__(self) -> None:
        for work in self._pending:  # a test that never settled: close quietly instead of warning "never awaited"
            work.close()
