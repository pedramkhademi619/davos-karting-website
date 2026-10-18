from __future__ import annotations

import uuid
from dataclasses import dataclass, field


@dataclass(frozen=True)
class BulkSmsReport:
    batch_id: uuid.UUID
    accepted: int
    failed: int
    invalid_numbers: list[str] = field(default_factory=list)
