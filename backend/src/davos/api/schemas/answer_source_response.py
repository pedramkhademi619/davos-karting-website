from pydantic import BaseModel


class AnswerSourceResponse(BaseModel):
    title: str
    url: str
