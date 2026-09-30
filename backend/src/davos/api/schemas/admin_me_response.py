import uuid

from pydantic import BaseModel


class AdminMeResponse(BaseModel):
    admin_id: uuid.UUID
    username: str
    display_name: str
    role: str
    csrf_token: str
