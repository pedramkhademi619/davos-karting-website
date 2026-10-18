from __future__ import annotations

from abc import ABC, abstractmethod

from davos.composition.status.probe_result import ProbeResult


class ServiceProbe(ABC):
    """One thing the site depends on. ``check`` must report problems as a result, not raise (the runner also guards)."""

    key: str
    group: str
    label: str
    cache_seconds: float = 0.0  # >0 for calls to third parties, so a busy panel does not hammer them

    @abstractmethod
    async def check(self) -> ProbeResult: ...
