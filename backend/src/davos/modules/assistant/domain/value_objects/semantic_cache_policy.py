from __future__ import annotations

from dataclasses import dataclass, field

from davos.modules.assistant.domain.enums.knowledge_source_type import KnowledgeSourceType


@dataclass(frozen=True)
class SemanticCachePolicy:
    """Every tunable of the semantic cache in one place (settings fill it in; the defaults are the safe ones)."""

    similarity_threshold: float = 0.94  # cosine similarity; measured, see docs/SEMANTIC_CACHE.md (0.88 misfires)
    candidate_limit: int = 8  # nearest entries fetched, then filtered by signature in code
    max_age_days: int = 30  # older entries are not served (they are purged later)
    # Answers that cite one of these kinds of source are never cached: a wrong "yes" to a safety rule would be repeated.
    excluded_source_types: frozenset[KnowledgeSourceType] = frozenset({KnowledgeSourceType.POLICY})
    min_answer_chars: int = 2
    max_embedding_text_chars: int = 400
    context_turns: int = 3  # exchanges remembered per conversation
    context_ttl_seconds: int = 1200
    context_max_answer_chars: int = 500
    extra_discriminator_words: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not 0.5 <= self.similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between 0.5 and 1.0")
        if self.candidate_limit < 1 or self.max_age_days < 1 or self.context_turns < 1:
            raise ValueError("candidate_limit, max_age_days and context_turns must be positive")
