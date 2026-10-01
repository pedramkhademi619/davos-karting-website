from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


@dataclass(frozen=True)
class AnswerCachePolicy:
    """The answer cache's tuning. The three numbers come from the settings (SEMANTIC_CACHE_*), measured with
    ``python -m davos.tools.evaluate_answer_cache``; the source-type rule is a design decision, not a setting."""

    similarity_threshold: float  # cosine similarity of the two questions; see docs/ASSISTANT_EVALUATION.md
    candidate_limit: int  # nearest stored answers fetched, then filtered by signature in code
    max_text_chars: int  # a question is embedded up to this length

    # An answer that cites one of these kinds of source is never stored: those are the riding rules, where a wrong
    # "yes" repeated to everybody is worse than one more model call.
    excluded_source_types: frozenset[KnowledgeSourceType] = frozenset({KnowledgeSourceType.POLICY})

    def __post_init__(self) -> None:
        if not 0.5 <= self.similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between 0.5 and 1.0")
        if self.candidate_limit < 1 or self.max_text_chars < 1:
            raise ValueError("candidate_limit and max_text_chars must be positive")
