import uuid
from datetime import datetime

from pydantic import BaseModel


class SessionResponse(BaseModel):
    session_id: uuid.UUID
    user_agent: str
    ip_hint: str
    created_at: datetime
    last_seen_at: datetime
    is_current: bool
