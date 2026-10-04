from pydantic import BaseModel


class CachedAnswerActiveRequest(BaseModel):
    active: bool
