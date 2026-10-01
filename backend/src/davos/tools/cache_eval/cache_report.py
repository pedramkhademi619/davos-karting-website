from __future__ import annotations

from collections.abc import Sequence

from davos.tools.cache_eval.cache_pair_result import CachePairResult
from davos.tools.cache_eval.pair_kind import PairKind

# 0.50 ... 0.98, then the levels where only near-identical questions remain
_THRESHOLDS = (*(round(0.5 + 0.02 * step, 2) for step in range(0, 25)), 0.99, 0.995, 1.0)
_FLOORS = (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)


class CacheReport:
    """The numbers that choose the cache's thresholds, from the pairs' results.

    A false hit is a look-alike pair with a different answer that the cache would serve (or an uncacheable question it
    would touch): the count that must be zero. Recall is how many paraphrases are answered from the cache.

    Without the model's check, the recommended threshold is the lowest one with no false hit and a safety margin above
    the most similar look-alike pair that the signature did not already separate, because a threshold that only just
    clears the pairs written here would not clear the next look-alike question a customer writes. With the check (a run
    with ``verified`` filled in) the table shows what each floor would add on top of the configured threshold."""

    MARGIN = 0.02

    def __init__(
        self, results: Sequence[CachePairResult], *, model: str, date: str, threshold: float, floor: float
    ) -> None:
        self._results = list(results)
        self._model = model
        self._date = date
        self._threshold = threshold
        self._floor = floor

    def _of(self, kind: PairKind) -> list[CachePairResult]:
        return [r for r in self._results if r.pair.kind is kind]

    @property
    def checked(self) -> bool:
        return any(r.verified is not None for r in self._results)

    def false_hits(self, threshold: float, floor: float | None = None) -> list[CachePairResult]:
        return [r for r in self._of(PairKind.DIFFERENT) if r.would_hit(threshold, floor)]

    def hits(self, threshold: float, floor: float | None = None) -> list[CachePairResult]:
        return [r for r in self._of(PairKind.SAME) if r.would_hit(threshold, floor)]

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
            f"**Recommended threshold without the model's check: {recommended:.2f}** (lowest with no false hit and a "
            f"{self.MARGIN:.2f} margin above the strongest look-alike that passes both rules: "
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
        if self.checked:
            lines += self._checked_section(same, different)
        touched = self.uncacheable_touched()
        lines += ["", f"## Uncacheable questions the cache would still look up: {len(touched)}", ""]
        lines += [f"- {r.pair.pair_id}: {r.pair.first} | {r.pair.second}" for r in touched]
        lines += ["", "## Paraphrases", "", "| Pair | Similarity | Cacheable | Same signature | Model check |"]
        lines.append("| --- | --- | --- | --- | --- |")
        for r in same:
            cacheable = "yes" if r.cacheable_first and r.cacheable_second else "NO"
            lines.append(
                f"| {r.pair.pair_id} {r.pair.first} / {r.pair.second} | {r.similarity:.3f} | {cacheable} | "
                f"{'yes' if r.same_signature else 'NO'} | {self._verdict(r)} |"
            )
        lines += ["", "## Look-alikes (must never be served for each other)", ""]
        lines += ["| Pair | Similarity | Stopped by |", "| --- | --- | --- |"]
        for r in different:
            lines.append(
                f"| {r.pair.pair_id} {r.pair.first} / {r.pair.second} | {r.similarity:.3f} | {self._stopped_by(r)} |"
            )
        return "\n".join(lines) + "\n"

    def _checked_section(self, same: list[CachePairResult], different: list[CachePairResult]) -> list[str]:
        threshold, floor = self._threshold, self._floor
        served = self.false_hits(threshold, floor)
        lines = [
            "",
            f"## With the model's check (threshold {threshold:.2f} as it is; checked from {floor:.2f} up)",
            "",
            f"**Paraphrases answered from the cache: {len(self.hits(threshold, floor))}/{len(same)}; "
            f"look-alikes served by mistake: {len(served)}/{len(different)}.**",
            "",
            "| Checked from | Paraphrases answered | False hits |",
            "| --- | --- | --- |",
        ]
        for candidate in _FLOORS:
            marker = " **←**" if candidate == floor else ""
            lines.append(
                f"| {candidate:.2f}{marker} | {len(self.hits(threshold, candidate))}/{len(same)} | "
                f"{len(self.false_hits(threshold, candidate))}/{len(different)} |"
            )
        lines += [""] + [f"- FALSE HIT {r.pair.pair_id}: {r.pair.first} | {r.pair.second}" for r in served]
        return lines

    @staticmethod
    def _verdict(result: CachePairResult) -> str:
        if result.verified is None:
            return "-"
        return "yes" if result.verified else "no"

    def _stopped_by(self, result: CachePairResult) -> str:
        if not (result.cacheable_first and result.cacheable_second):
            return "the eligibility rule (age, day, hour, ... in one question)"
        if not result.same_signature:
            return "the signature (a deciding word differs)"
        if result.verified is True:
            return "NOTHING but the similarity: the model said yes"
        if result.verified is False:
            return "the model's check (it said no)"
        return "the similarity threshold only"
