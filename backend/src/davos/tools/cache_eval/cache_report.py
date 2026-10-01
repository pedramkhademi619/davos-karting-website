from __future__ import annotations

from collections.abc import Sequence

from davos.tools.cache_eval.cache_pair_result import CachePairResult
from davos.tools.cache_eval.pair_kind import PairKind

_THRESHOLDS = tuple(round(0.5 + 0.02 * step, 2) for step in range(0, 25))  # 0.50 ... 0.98


class CacheReport:
    """The numbers that choose the similarity threshold, from the pairs' results.

    A false hit is a look-alike pair with a different answer that the cache would serve (or an uncacheable question it
    would touch): the count that must be zero. Recall is how many paraphrases are answered from the cache. The
    recommended threshold is the lowest one with no false hit and a safety margin above the most similar look-alike pair
    that the signature did not already separate, because a threshold that only just clears the pairs written here would
    not clear the next look-alike question a customer writes."""

    MARGIN = 0.02

    def __init__(self, results: Sequence[CachePairResult], *, model: str, date: str) -> None:
        self._results = list(results)
        self._model = model
        self._date = date

    def _of(self, kind: PairKind) -> list[CachePairResult]:
        return [r for r in self._results if r.pair.kind is kind]

    def false_hits(self, threshold: float) -> list[CachePairResult]:
        return [r for r in self._of(PairKind.DIFFERENT) if r.would_hit(threshold)]

    def hits(self, threshold: float) -> list[CachePairResult]:
        return [r for r in self._of(PairKind.SAME) if r.would_hit(threshold)]

    def strongest_look_alike(self) -> float | None:
        """The highest similarity among look-alike pairs that both rules (eligibility, signature) let through."""
        eligible = [r.similarity for r in self._of(PairKind.DIFFERENT) if r.eligible]
        return max(eligible, default=None)

    def recommended_threshold(self) -> float:
        strongest = self.strongest_look_alike()
        floor = 0.5 if strongest is None else strongest + self.MARGIN
        return min(1.0, next((t for t in _THRESHOLDS if t >= floor), 1.0))

    def uncacheable_touched(self) -> list[CachePairResult]:
        """Pairs that must stay out of the cache but where a question would still be looked up."""
        return [r for r in self._of(PairKind.UNCACHEABLE) if r.cacheable_first or r.cacheable_second]

    def markdown(self) -> str:
        same, different = self._of(PairKind.SAME), self._of(PairKind.DIFFERENT)
        recommended = self.recommended_threshold()
        strongest = self.strongest_look_alike()
        lines = [
            "# Answer cache evaluation",
            "",
            f"{self._date} · embedding model `{self._model}` · {len(same)} paraphrase pairs, {len(different)} "
            f"look-alike pairs, {len(self._of(PairKind.UNCACHEABLE))} uncacheable pairs",
            "",
            f"**Recommended threshold: {recommended:.2f}** (lowest with no false hit and a {self.MARGIN:.2f} "
            f"margin above the strongest look-alike that passes both rules: "
            f"{'none' if strongest is None else f'{strongest:.3f}'}).",
            "",
            "| Threshold | Paraphrases answered from the cache | False hits (look-alikes served) |",
            "| --- | --- | --- |",
        ]
        for threshold in _THRESHOLDS:
            marker = " **←**" if threshold == recommended else ""
            lines.append(
                f"| {threshold:.2f}{marker} | {len(self.hits(threshold))}/{len(same)} | "
                f"{len(self.false_hits(threshold))}/{len(different)} |"
            )
        touched = self.uncacheable_touched()
        lines += ["", f"## Uncacheable questions the cache would still look up: {len(touched)}", ""]
        lines += [f"- {r.pair.pair_id}: {r.pair.first} | {r.pair.second}" for r in touched]
        lines += [
            "",
            "## Paraphrases",
            "",
            "| Pair | Similarity | Cacheable | Same signature |",
            "| --- | --- | --- | --- |",
        ]
        for r in same:
            cacheable = "yes" if r.cacheable_first and r.cacheable_second else "NO"
            lines.append(
                f"| {r.pair.pair_id} {r.pair.first} / {r.pair.second} | {r.similarity:.3f} | {cacheable} | "
                f"{'yes' if r.same_signature else 'NO'} |"
            )
        lines += [
            "",
            "## Look-alikes (must never be served for each other)",
            "",
            "| Pair | Similarity | Stopped by |",
            "| --- | --- | --- |",
        ]
        for r in different:
            stopped = "the similarity threshold only" if r.eligible else self._stopped_by(r)
            lines.append(f"| {r.pair.pair_id} {r.pair.first} / {r.pair.second} | {r.similarity:.3f} | {stopped} |")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _stopped_by(result: CachePairResult) -> str:
        if not (result.cacheable_first and result.cacheable_second):
            return "the eligibility rule (age, day, hour, ... in one question)"
        return "the signature (a deciding word differs)"
