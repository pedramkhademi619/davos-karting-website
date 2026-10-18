from __future__ import annotations

import re

from davos.tools.assistant_eval.grading_text import GradingText
from davos.tools.assistant_eval.verdict import Verdict

_SENTENCE_END = re.compile(r"[.!?؟؛;\n]")
_B = r"(?:^|(?<=[^\w]))"  # start of a word (Persian letters count as word characters)
_E = r"(?=[^\w]|$)"
_YES = re.compile(
    rf"{_B}(?:آره|اره|بله|بلی|حتما|قطعا|میتون\w*|میشه|میشود|میتوان\w*|امکانپذیر(?:ه| است)|مجازه|مجاز است|"
    rf"مشکلی نیست|مشکلی نداره|اشکالی نداره|کافیه|کافی است|yes|sure|of course|can){_E}"
)
# "مشکلی نیست؟" -> "نه، مشکلی نیست": a "no" that means yes.
_NO_PROBLEM = re.compile(rf"{_B}نه\W*(?:هیچ\s*)?(?:مشکلی|اشکالی)\s*(?:نیست|نداره|ندارد){_E}")
_NO = re.compile(
    rf"{_B}(?:نه|خیر|نمی\w*|متاسفانه|امکانش نیست|امکان ندار\w*|امکانپذیر نیست|مجاز نیست|اجازه ندار\w*|"
    rf"no|not|cannot|can't|unfortunately){_E}"
)


class VerdictClassifier:
    """Reads the verdict from a reply's first sentence, where the persona puts it ("آره، می‌تونه!", "نه، نمی‌تونه؛").

    Whichever of a yes or a no marker comes first in that sentence wins; nothing found is UNCLEAR, which fails a
    yes/no case on purpose: a customer who has to read three sentences to learn the answer was not answered well.
    """

    def classify(self, text: str) -> Verdict:
        normalized = GradingText.normalize(text)
        sentences = [s for s in _SENTENCE_END.split(normalized) if s.strip()]
        lead = sentences[0] if sentences else ""
        if len(lead) < 12 and len(sentences) > 1:  # "نه!" / "آره." followed by the reason
            lead = f"{lead} {sentences[1]}"
        if _NO_PROBLEM.search(lead):
            return Verdict.YES
        yes, no = _YES.search(lead), _NO.search(lead)
        if yes and (not no or yes.start() < no.start()):
            return Verdict.YES
        if no:
            return Verdict.NO
        return Verdict.UNCLEAR
