from __future__ import annotations

from collections.abc import Sequence

from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate


class CacheHitSelector:
    """Which stored answers may be considered for a question: the ones with the same signature (the same numbers and
    deciding words), the most similar first. Whether one of them is similar enough is the cache's decision."""

    def matching(self, candidates: Sequence[CacheCandidate], *, signature: str) -> list[CacheCandidate]:
        same = [c for c in candidates if c.signature == signature]
        return sorted(same, key=lambda candidate: candidate.similarity, reverse=True)
