import uuid

from pydantic import BaseModel, ConfigDict, Field


class AskAssistantRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000, description="Trimmed and length-checked again by the domain")
    conversation_id: uuid.UUID | None = None
    consent_to_store: bool = Field(
        default=False, description="Explicit opt-in to store this question and answer for quality review."
    )
