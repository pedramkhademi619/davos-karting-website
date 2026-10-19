from typing import Literal

from pydantic import BaseModel, Field


class GuideMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=1500)


class AdminGuideRequest(BaseModel):
    """The conversation so far, oldest first; the last message is the new question."""

    messages: list[GuideMessage] = Field(min_length=1, max_length=12)
