from __future__ import annotations

import re

from davos.modules.assistant.domain.value_objects.discriminator_lexicon import DISCRIMINATOR_WORDS, word_set
from davos.modules.assistant.domain.value_objects.persian_stopwords import PERSIAN_STOPWORDS
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer

_MAX_WORDS = 6
_MAX_CONTENT_WORDS = 3
# Words that point back at something said earlier ("its price", "that one", "and Thursday?").
_POINTERS = word_set(
    "این اون آن همین همون اینو اونو اینا اونا اینها اونها آنها ایشون او it its that this those these them they "
    "هذا هذه ذلک تلک"
)
# "هزینه‌ش" is "هزینه" + ZWNJ + "ش", which the normaliser splits into a lone clitic.
_CLITICS = word_set("ش شو شون شم شه")
_NOUN_WITH_CLITIC = re.compile(
    r"(?<!\w)(?:قیمت|هزینه|ساعت|شرایط|آدرس|شماره|ظرفیت|زمان|وقت|سن|قد|وزن)(?:ش|شو|شون)(?!\w)"
)
_CONNECTORS = word_set("و پس یعنی ولی اما خب and so then but also")
# Question particles say nothing about the topic, so "پنجشنبه چطوره" has one content word, not two.
_PARTICLES = word_set("چطوره چیه چیست چنده چقدره کجاست کیه چجوری چه")


class FollowUpDetector:
    """Decides whether a short message only makes sense next to the previous one ("هزینه‌ش چقدره؟", "و پنجشنبه؟").

    A heuristic, not understanding: it looks for words that point backwards, a leading "and/so", or a message made
    only of details (a day, a number). A wrong answer is harmless: a follow-up taken for a fresh question merely
    misses the cache and reaches the model together with the conversation history; the reverse merely builds a
    longer query.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def is_follow_up(self, text: str) -> bool:
        normalized = self._normalizer.normalize(text)
        words = normalized.split()
        if not words or len(words) > _MAX_WORDS:
            return False
        if any(word in _POINTERS or word in _CLITICS for word in words) or _NOUN_WITH_CLITIC.search(normalized):
            return True
        if words[0] in _CONNECTORS:
            return True
        content = [w for w in words if w not in PERSIAN_STOPWORDS and w not in _PARTICLES]
        return 0 < len(content) <= _MAX_CONTENT_WORDS and all(w in DISCRIMINATOR_WORDS or w.isdigit() for w in content)
