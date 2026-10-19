from pydantic import BaseModel, Field

from davos.api.schemas.guide_message import GuideMessage


class AdminGuideRequest(BaseModel):
    """The conversation so far, oldest first; the last message is the new question."""

    messages: list[GuideMessage] = Field(min_length=1, max_length=12)
