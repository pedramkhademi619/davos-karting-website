from pydantic import BaseModel, ConfigDict


class AssistantFeedbackRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    helpful: bool
