from __future__ import annotations

from dataclasses import dataclass

from davos.modules.assistant.domain.value_objects.query_embedding import QueryEmbedding


@dataclass(frozen=True)
class CacheProbe:
    """One question prepared for the cache: what was embedded, the details that must match, and what the answer
    would depend on. Made once per question and used for the lookup and, after a model answer, the store."""

    text: str  # the normalised question that was embedded
    embedding: QueryEmbedding
    signature: str
    fingerprint: str
