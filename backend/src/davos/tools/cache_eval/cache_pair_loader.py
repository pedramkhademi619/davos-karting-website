from __future__ import annotations

import json
from pathlib import Path

from davos.tools.cache_eval.cache_pair import CachePair
from davos.tools.cache_eval.pair_kind import PairKind


class CachePairLoader:
    """Reads the pairs: one JSON object per line (id, kind, a, b); ``#`` lines and blank lines are ignored. A mistake
    stops the run with its line number, so two runs are always over the same pairs."""

    def load(self, path: Path) -> list[CachePair]:
        pairs: list[CachePair] = []
        seen: set[str] = set()
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            try:
                raw = json.loads(stripped)
                pair = CachePair(
                    str(raw["id"]), PairKind(str(raw["kind"])), str(raw["a"]).strip(), str(raw["b"]).strip()
                )
                if not pair.first or not pair.second:
                    raise ValueError("empty question")
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"{path.name}:{number}: {exc}") from exc
            if pair.pair_id in seen:
                raise ValueError(f"{path.name}:{number}: duplicate id {pair.pair_id}")
            seen.add(pair.pair_id)
            pairs.append(pair)
        return pairs
