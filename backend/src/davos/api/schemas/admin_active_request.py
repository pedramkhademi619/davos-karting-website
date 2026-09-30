from pydantic import BaseModel


class AdminActiveRequest(BaseModel):
    is_active: bool
