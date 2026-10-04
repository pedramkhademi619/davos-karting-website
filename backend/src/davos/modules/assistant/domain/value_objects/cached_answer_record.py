from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CachedAnswerRecord:
    """A stored answer as the owner sees it in the review screen."""

    entry_id: uuid.UUID
    question: str
    answer: str
    hit_count: int
    is_active: bool
    is_curated: bool  # written or approved by the owner: kept until the owner changes it
    created_at: datetime
    last_used_at: datetime
