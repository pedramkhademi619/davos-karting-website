import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticatedCustomer:
    user_id: uuid.UUID
    session_id: uuid.UUID
