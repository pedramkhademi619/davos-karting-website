from typing import Literal

from pydantic import BaseModel, Field


class GuideMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=1500)
