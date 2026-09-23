import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VerifyOtpResult:
    user_id: uuid.UUID
    session_id: uuid.UUID
    session_token: str
    expires_at: datetime
    is_new_user: bool
