from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeEntryRequest(BaseModel):
    source_type: Literal["faq", "policy", "service", "pricing", "contact"]
    title: str = Field(max_length=300)
    body: str = Field(max_length=4000)
    url: str = Field(max_length=300)
