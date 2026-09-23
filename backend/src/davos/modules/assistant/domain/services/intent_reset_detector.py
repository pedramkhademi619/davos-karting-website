from __future__ import annotations

import re

from davos.modules.assistant.domain.value_objects.intent_reset_verdict import IntentResetVerdict
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

# Patterns run on normalised text (Persian letter forms, no punctuation, lower case), so "فراموشش کن!" and "Never mind."
# are matched as they are written here.
_PHRASES = (
    # Persian
    r"فراموش(?:ش)?\s*کن(?:ید)?",
    r"بی\s*خیال(?:ش)?(?:\s*شو(?:ید)?)?(?:\s*قبلی)?",
    r"ولش\s*کن(?:ید)?",
    r"(?:از\s*)?اول\s*شروع\s*کن(?:یم|ید)?",
    r"شروع\s*از\s*اول",
    r"(?:موضوع|بحث)\s*(?:را|رو)?\s*عوض\s*کن(?:یم|ید)?",
    r"(?:یه|یک)?\s*سوال\s*(?:جدید|دیگه|دیگر)(?:\s*ای)?(?:\s*دارم)?",
    # Arabic
    r"انسی\s*(?:ذلک|الامر|ما\s*سبق|السابق)",
    r"تجاهل\s*(?:ما\s*سبق|السابق|الرسائل\s*السابقه)",
    r"لا\s*یهم",
    r"ابدا\s*من\s*جدید",
    r"موضوع\s*جدید",
    # English
    r"never\s*mind",
    r"forget\s+(?:it|that|about\s+it|the\s+previous(?:\s+context)?|previous(?:\s+context)?)",
    r"ignore\s+(?:the\s+)?(?:previous|prior|earlier)\s+(?:context|conversation|question|messages?)",
    r"start\s+over",
    r"new\s+topic",
    r"reset\s+(?:the\s+)?(?:conversation|context)",
)
_RESET = re.compile(r"(?:" + "|".join(_PHRASES) + r")(?!\w)")
_LEADING_CONNECTORS = re.compile(r"^(?:و|بعد|حالا|خب|خوب|ok|okay|so|now|and|but|ولی|اما)\s+")
_MIN_WORDS_FOR_A_NEW_QUESTION = 2


class IntentResetDetector:
    """Spots "forget that / never mind / start over" in Persian, Arabic and English.

    The command must open the message (after an "ok" or "و"): "start over" inside "how do I start over a failed booking"
    is part of a real question and is left alone. A message that is only the command resets the conversation; a
    command followed by a real question resets it and hands back the question ("بی‌خیال قبلی، ساعت کاری چیه؟" ->
    "ساعت کاری چیه"). Pure regular expressions, no model.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def detect(self, text: str) -> IntentResetVerdict:
        body = self._without_leading_connectors(self._normalizer.normalize(text))
        match = _RESET.match(body)
        if match is None:
            return IntentResetVerdict(reset=False)
        remainder = self._without_leading_connectors(body[match.end() :].strip())
        if len(remainder.split()) < _MIN_WORDS_FOR_A_NEW_QUESTION:
            remainder = ""
        return IntentResetVerdict(reset=True, remainder=remainder)

    @staticmethod
    def _without_leading_connectors(text: str) -> str:
        while _LEADING_CONNECTORS.match(text):
            text = _LEADING_CONNECTORS.sub("", text, count=1)
        return text
