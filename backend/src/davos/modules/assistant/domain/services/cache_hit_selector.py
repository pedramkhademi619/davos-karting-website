from __future__ import annotations

from collections.abc import Sequence

from davos.modules.assistant.domain.value_objects.cache_candidate import CacheCandidate


class CacheHitSelector:
    """Chooses which stored entry, if any, may answer a question.

    An entry qualifies only when it is similar enough *and* carries the same signature (same numbers and same
    discriminator words); among those the most similar wins.
    """

    def select(
        self, candidates: Sequence[CacheCandidate], *, signature: str, threshold: float
    ) -> CacheCandidate | None:
        eligible = [c for c in candidates if c.signature == signature and c.similarity >= threshold]
        return max(eligible, key=lambda candidate: candidate.similarity, default=None)
