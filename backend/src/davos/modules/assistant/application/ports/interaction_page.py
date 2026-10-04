from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.reviewed_interaction import ReviewedInteraction


@dataclass(frozen=True)
class InteractionPage:
    items: list[ReviewedInteraction]
    total: int
