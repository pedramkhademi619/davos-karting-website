from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    message: str
