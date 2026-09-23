from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Immutable fact that happened inside an aggregate.

    Events are carried out of the domain by the aggregate root and persisted through the
    transactional outbox in the same transaction as the state change.
    """

    occurred_at: datetime
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)

    @property
    def event_name(self) -> str:
        parts = type(self).__module__.split(".")
        module = parts[parts.index("modules") + 1] if "modules" in parts else "shared"
        return f"{module}.{type(self).__name__}"
