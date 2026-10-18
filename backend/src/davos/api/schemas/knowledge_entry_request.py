from typing import Literal

from pydantic import BaseModel, Field


class KnowledgeEntryRequest(BaseModel):
    source_type: Literal["faq", "policy", "service", "pricing", "contact"] = "faq"  # optional in the panel
    title: str = Field(max_length=300)
    body: str = Field(max_length=4000)
    url: str = Field(default="/", max_length=300)  # optional in the panel: "/" = no particular page
