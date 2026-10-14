from pydantic import BaseModel


class ServicePartResponse(BaseModel):
    label: str
    level: str
    detail: str
