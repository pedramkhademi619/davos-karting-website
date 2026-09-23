from __future__ import annotations

import re

from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer
from davos.modules.assistant.domain.value_objects.screening_verdict import ScreeningVerdict

_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "override_instructions",
        re.compile(
            r"(ignore|disregard|forget|override)\W+(all\W+|any\W+|the\W+)?(previous|prior|above|earlier|system)\W+"
            r"(instructions?|prompts?|rules?)",
            re.I,
        ),
    ),
    (
        "override_instructions_fa",
        re.compile(
            r"((دستور|دستورات|دستورالعمل|قوانین|قانون|پیام)\S*\s+(قبلی|بالا|سیستم|اولیه)\S*\s+(را\s+)?(نادیده|فراموش|کنار)"
            r"|(نادیده\s*بگیر|فراموش\s*کن)\S*\s+(همه\s+)?(دستور|دستورات|دستورالعمل|قوانین|قانون)\S*)"
        ),
    ),
    (
        "reveal_prompt",
        re.compile(
            r"(reveal|show|print|repeat|leak|tell me)\W+.{0,30}(system\W+prompt|instructions|hidden\W+rules)", re.I
        ),
    ),
    ("reveal_prompt_fa", re.compile(r"(پرامپت|پرومپت|دستورالعمل|قوانین)\s*(سیستم|داخلی|مخفی|اولیه)")),
    (
        "role_hijack",
        re.compile(r"(you\s+are\s+now|act\s+as|pretend\s+(to\s+be|you\s+are)|jailbreak|developer\s+mode)", re.I),
    ),
    ("role_hijack_fa", re.compile(r"(از\s+الان\s+تو|تو\s+الان|نقش\s+.{0,20}\s*بازی\s*کن|فرض\s+کن\s+که\s+تو)")),
    ("fake_role_markup", re.compile(r"(^|\n)\s*(system|assistant|developer)\s*:", re.I)),
    (
        "delimiter_break",
        re.compile(r"</?\s*(passage|question|system|instructions?|history|style|customer|assistant)\b", re.I),
    ),
    ("tool_or_secret_request", re.compile(r"(api[\s_-]?key|secret[\s_-]?key|کلید\s*api)", re.I)),
)


class PromptInjectionScreen:
    """Cheap heuristic pre-filter for obvious injection attempts.

    It is one layer of defence, not the defence: retrieved text and the question are also
    delimited and declared as data, the model has no tools, and the output is re-validated.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def assess(self, text: str) -> ScreeningVerdict:
        """Match against the raw text and its Persian-normalised form (defeats letter-variant evasion)."""
        variants = (text, self._normalizer.normalize(text))
        reasons = tuple(name for name, pattern in _RULES if any(pattern.search(v) for v in variants))
        return ScreeningVerdict(suspicious=bool(reasons), reasons=reasons)
