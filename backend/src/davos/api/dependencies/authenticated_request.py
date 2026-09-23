import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedRequest:
    user_id: uuid.UUID
    session_id: uuid.UUID
    csrf_token: str
