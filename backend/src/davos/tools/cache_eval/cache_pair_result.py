from __future__ import annotations

from dataclasses import dataclass

from davos.tools.cache_eval.cache_pair import CachePair


@dataclass(frozen=True)
class CachePairResult:
    """What the cache's rules say about one pair: would the second question be answered from the first one's entry?"""

    pair: CachePair
    similarity: float  # cosine similarity of the two questions' embeddings
    cacheable_first: bool
    cacheable_second: bool
    same_signature: bool

    @property
    def eligible(self) -> bool:
        """Everything except the similarity threshold allows it."""
        return self.cacheable_first and self.cacheable_second and self.same_signature

    def would_hit(self, threshold: float) -> bool:
        return self.eligible and self.similarity >= threshold
