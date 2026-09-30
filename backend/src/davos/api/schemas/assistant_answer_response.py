import uuid

from pydantic import BaseModel

from davos.api.schemas.answer_source_response import AnswerSourceResponse


class AssistantAnswerResponse(BaseModel):
    answer: str
    outcome: str
    sources: list[AnswerSourceResponse]
    suggest_ticket: bool
    interaction_id: uuid.UUID | None
