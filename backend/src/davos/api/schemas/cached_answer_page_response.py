from pydantic import BaseModel

from davos.api.schemas.cached_answer_response import CachedAnswerResponse


class CachedAnswerPageResponse(BaseModel):
    items: list[CachedAnswerResponse]
    total: int
