from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SessionSummary:
    session_id: uuid.UUID
    user_agent: str
    ip_hint: str
    created_at: datetime
    last_seen_at: datetime
    is_current: bool
