import uuid
from datetime import datetime

from pydantic import BaseModel


class SignedInResponse(BaseModel):
    user_id: uuid.UUID
    is_new_user: bool
    expires_at: datetime
    csrf_token: str
