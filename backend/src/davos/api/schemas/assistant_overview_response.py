from __future__ import annotations

from pydantic import BaseModel

from davos.modules.assistant.domain.value_objects.assistant_overview import AssistantOverview


class AssistantOverviewResponse(BaseModel):
    days: int
    questions: int
    by_outcome: dict[str, int]
    served_from_cache: int
    helpful_votes: int
    not_helpful_votes: int
    prompt_tokens: int
    completion_tokens: int
    cached_answers_active: int
    cached_answers_total: int
    knowledge_entries: int

    @classmethod
    def of(cls, overview: AssistantOverview) -> AssistantOverviewResponse:
        return cls(
            days=overview.days,
            questions=overview.questions,
            by_outcome=dict(overview.by_outcome),
            served_from_cache=overview.served_from_cache,
            helpful_votes=overview.helpful_votes,
            not_helpful_votes=overview.not_helpful_votes,
            prompt_tokens=overview.prompt_tokens,
            completion_tokens=overview.completion_tokens,
            cached_answers_active=overview.cached_answers_active,
            cached_answers_total=overview.cached_answers_total,
            knowledge_entries=overview.knowledge_entries,
        )
