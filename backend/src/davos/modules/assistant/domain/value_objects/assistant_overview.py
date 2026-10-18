from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class AssistantOverview:
    """What the assistant did over the last ``days`` days, for the owner's review screen."""

    days: int
    questions: int
    by_outcome: Mapping[str, int]
    served_from_cache: int
    helpful_votes: int
    not_helpful_votes: int
    prompt_tokens: int
    completion_tokens: int
    cached_answers_active: int
    cached_answers_total: int
    knowledge_entries: int
