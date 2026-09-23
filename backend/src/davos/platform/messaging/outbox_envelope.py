import uuid
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OutboxEnvelope:
    event_id: uuid.UUID
    event_name: str
    payload: dict[str, Any]
