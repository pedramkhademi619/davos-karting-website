from __future__ import annotations

from dataclasses import dataclass

from davos.tools.cache_eval.cache_pair import CachePair


@dataclass(frozen=True)
class CachePairResult:
    """What the cache's rules say about one pair: would the second question be answered from the first one's entry?

    ``verified`` is the language model's answer to "does one answer fit both questions?", asked for pairs that pass the
    other rules when the evaluation runs with the check on; None when it was not asked."""

    pair: CachePair
    similarity: float  # cosine similarity of the two questions' embeddings
    cacheable_first: bool
    cacheable_second: bool
    same_signature: bool
    verified: bool | None = None

    @property
    def eligible(self) -> bool:
        """Everything except the similarity threshold and the model's check allows it."""
        return self.cacheable_first and self.cacheable_second and self.same_signature

    def would_hit(self, threshold: float, floor: float | None = None) -> bool:
        """Served at ``threshold`` and above as it is; between ``floor`` and the threshold only if the model agreed."""
        if not self.eligible:
            return False
        if self.similarity >= threshold:
            return True
        return floor is not None and self.verified is True and self.similarity >= floor
