from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from davos.modules.assistant.domain.errors.question_rejected_error import QuestionRejectedError

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f‪-‮⁦-⁩]")
_SPACES = re.compile(r"[ \t\r\n]+")


@dataclass(frozen=True)
class Question:
    """A validated, cleaned customer question. Always treated as untrusted data."""

    text: str

    @classmethod
    def create(cls, raw: str, *, max_chars: int) -> Question:
        cleaned = _SPACES.sub(" ", _CONTROL.sub("", unicodedata.normalize("NFC", raw))).strip()
        if len(cleaned) < 2:
            raise QuestionRejectedError("لطفا پرسش خود را بنویسید.")
        if len(cleaned) > max_chars:
            raise QuestionRejectedError(f"پرسش نباید بیشتر از {max_chars} نویسه باشد.", code="question_too_long")
        return cls(cleaned)
