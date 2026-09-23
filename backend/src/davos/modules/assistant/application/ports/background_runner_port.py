from abc import ABC, abstractmethod
from collections.abc import Coroutine
from typing import Any


class BackgroundRunnerPort(ABC):
    @abstractmethod
    def run(self, work: Coroutine[Any, Any, None], *, name: str) -> None:
        """Starts ``work`` without making the caller wait. A failure is logged and never reaches the caller."""
