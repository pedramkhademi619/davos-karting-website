from pydantic import BaseModel, Field


class CuratedAnswerRequest(BaseModel):
    question: str = Field(max_length=400)
    answer: str = Field(max_length=2000)
