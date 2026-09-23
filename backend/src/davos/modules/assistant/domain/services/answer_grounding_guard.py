from __future__ import annotations

import re
from collections.abc import Sequence

from davos.modules.assistant.domain.enums.grounding_kind import GroundingKind
from davos.modules.assistant.domain.value_objects.grounding_result import GroundingResult

NO_ANSWER_TOKEN = "NO_ANSWER"  # noqa: S105 - marker, not a credential

_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]*)\)")
_CITATION = re.compile(r"\[(\d{1,2})\]")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
_SPACES = re.compile(r"[ \t]{2,}")
_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([.،؛؟!:])")  # what removing "[1]" leaves behind


class AnswerGroundingGuard:
    """Validates the model output before anything reaches a customer.

    * refuses to show text that leaks the hidden prompt (canary / rule fingerprints),
    * treats an answer without any valid citation as ungrounded and discards it,
    * removes every URL the model wrote (only sources we retrieved are ever linked).
    """

    def __init__(self, *, max_chars: int) -> None:
        self._max_chars = max_chars

    def evaluate(self, raw: str, *, passage_count: int, canary: str, leak_markers: Sequence[str]) -> GroundingResult:
        text = raw.strip()
        if canary and canary in text:
            return GroundingResult(GroundingKind.LEAK)
        if any(marker in text for marker in leak_markers):
            return GroundingResult(GroundingKind.LEAK)
        if not text or text.upper().startswith(NO_ANSWER_TOKEN):
            return GroundingResult(GroundingKind.NO_ANSWER)

        text = _MARKDOWN_LINK.sub(r"\1", text)
        cited = tuple(sorted({int(n) for n in _CITATION.findall(text) if 1 <= int(n) <= passage_count}))
        if not cited:
            return GroundingResult(GroundingKind.UNGROUNDED)

        cleaned = _URL.sub("", _CITATION.sub("", text))
        cleaned = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", _SPACES.sub(" ", cleaned).strip())
        if not cleaned:
            return GroundingResult(GroundingKind.UNGROUNDED)
        return GroundingResult(GroundingKind.GROUNDED, text=self._truncate(cleaned), cited_indices=cited)

    def _truncate(self, text: str) -> str:
        if len(text) <= self._max_chars:
            return text
        cut = text[: self._max_chars]
        boundary = max(cut.rfind("."), cut.rfind("؟"), cut.rfind("!"), cut.rfind("؛"))
        return (cut[: boundary + 1] if boundary > self._max_chars // 2 else cut.rstrip()) or cut
