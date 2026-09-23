from __future__ import annotations

import dataclasses
import uuid
from datetime import datetime
from typing import Any

from davos.shared_kernel.domain.domain_event import DomainEvent


class EventSerializer:
    """DomainEvent -> JSON-safe dict. Only plain data leaves the domain."""

    def serialize(self, event: DomainEvent) -> dict[str, Any]:
        return {key: self._plain(value) for key, value in dataclasses.asdict(event).items()}

    def _plain(self, value: Any) -> Any:
        if isinstance(value, uuid.UUID):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, dict):
            return {k: self._plain(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self._plain(v) for v in value]
        return value
