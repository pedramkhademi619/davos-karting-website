from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class JudgeVerdict:
    """A second model's binary opinion of one reply (binary criteria agree better between judges than 1-10 scores)."""

    correct: bool  # the decision and the facts match the knowledge and the expected label
    faithful: bool  # every claim is supported by the knowledge; nothing invented
    helpful: bool  # answers what was asked, verdict first, offers the allowed alternative when saying no
    natural: bool  # natural, polite colloquial Persian; no robotic template, no needless question
    rationale: str
