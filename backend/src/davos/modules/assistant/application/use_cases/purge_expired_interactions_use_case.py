from __future__ import annotations

from davos.modules.assistant.application.ports.interaction_log_port import InteractionLogPort
from davos.shared_kernel.application.clock import Clock


class PurgeExpiredInteractionsUseCase:
    """Retention enforcement, run daily by the scheduler."""

    def __init__(self, *, interactions: InteractionLogPort, clock: Clock) -> None:
        self._interactions = interactions
        self._clock = clock

    async def execute(self) -> int:
        return await self._interactions.purge_expired(self._clock.now())
