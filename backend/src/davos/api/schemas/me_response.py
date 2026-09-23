import uuid

from pydantic import BaseModel


class MeResponse(BaseModel):
    user_id: uuid.UUID
    csrf_token: str
