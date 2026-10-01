from __future__ import annotations

from dataclasses import dataclass

from davos.tools.cache_eval.pair_kind import PairKind


@dataclass(frozen=True)
class CachePair:
    pair_id: str
    kind: PairKind
    first: str
    second: str
