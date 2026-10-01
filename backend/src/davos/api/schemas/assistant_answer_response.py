import uuid

from pydantic import BaseModel

from davos.api.schemas.answer_source_response import AnswerSourceResponse


class AssistantAnswerResponse(BaseModel):
    answer: str
    outcome: str
    sources: list[AnswerSourceResponse]
    suggest_ticket: bool
    interaction_id: uuid.UUID | None
    from_cache: bool  # a stored answer to a question that means the same: no model call, no wait
