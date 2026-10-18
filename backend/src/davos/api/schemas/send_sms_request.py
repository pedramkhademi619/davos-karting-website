from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SendSmsRequest(BaseModel):
    """Who receives the text: typed numbers, everyone who agreed to news, or the customers of one day."""

    audience: Literal["numbers", "subscribers", "day"]
    numbers: list[str] = Field(default_factory=list, max_length=5000)
    day: date | None = None
    text: str = Field(min_length=1, max_length=600)
