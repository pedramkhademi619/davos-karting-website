from __future__ import annotations

from davos.modules.assistant.domain.enums.quick_topic import QuickTopic
from davos.modules.assistant.domain.value_objects.persian_text_normalizer import PersianTextNormalizer


def _words(text: str) -> frozenset[str]:
    return frozenset(text.split())


def _phrases(*phrases: str) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(phrase.split()) for phrase in phrases)


# The normalizer turns a half-space into a space, so «قیمت‌ها» is «قیمت ها» here.
_TOPIC_PHRASES: dict[QuickTopic, tuple[tuple[str, ...], ...]] = {
    QuickTopic.HOURS: _phrases(
        "ساعت کاری",
        "ساعات کاری",
        "ساعت کار",
        "ساعات کار",
        "ساعت فعالیت",
        "ساعت باز",
        "چه ساعتی باز",
        "تا چه ساعتی",
        "ساعت کاریتون",
        "ساعت کاریتان",
        "بازید",
        "بازین",
    ),
    QuickTopic.BOOKING: _phrases("رزرو", "نوبت", "شماره", "شماره تماس", "شماره تلفن", "شماره موبایل", "تلفن"),
    QuickTopic.CAPACITY: _phrases(
        "ظرفیت", "چند نفر", "چند خودرو", "چند ماشین", "چند تا خودرو", "چند تا ماشین", "تعداد خودرو", "تعداد ماشین"
    ),
    QuickTopic.PRICES: _phrases("قیمت", "قیمت ها", "هزینه", "هزینه ها", "تعرفه", "نرخ", "چند تومان"),
    QuickTopic.CLUB: _phrases("باشگاه", "باشگاه مشتریان", "عضویت"),
}
# Words that may surround a topic phrase without adding a detail (a day, an hour, a car type, an age...) that would
# change the answer.
_FILLERS = _words(
    "سلام درود hi hello چیه چیست چی چقدره چقدر چند چه چطور چطوری چجوری چگونه میشه می شه شه است هست هستید هستین "
    "هستن هستند دارید دارین دارم میخوام می خوام میخواستم می خواستم بدونم بدانم بگید بگین بفرمایید لطفا یه یک "
    "برای ما شما رو را و یا با از به در کنم کنیم بگیرم بگیریم بشه بشن باید میتونم می تونم میتونیم می تونیم "
    "می تونن میتونن می ممکنه سوار کجا تون تان ها"
)
_MAX_WORDS = 9


class QuickTopicDetector:
    """Recognises a plain, general question about one topic that a single published entry answers completely.

    Strict on purpose: the question may contain only the topic phrase and neutral filler words. Anything that adds a
    detail (a day, an age, a car type...), or touches two topics, is not recognised and goes through the normal flow.
    """

    def __init__(self, normalizer: PersianTextNormalizer | None = None) -> None:
        self._normalizer = normalizer or PersianTextNormalizer()

    def detect(self, text: str) -> QuickTopic | None:
        words = self._normalizer.normalize(text).split()
        if not words or len(words) > _MAX_WORDS:
            return None
        matched: dict[QuickTopic, frozenset[str]] = {}
        for topic, phrases in _TOPIC_PHRASES.items():
            found = [phrase for phrase in phrases if self._contains(words, phrase)]
            if found:
                matched[topic] = frozenset(word for phrase in found for word in phrase)
        if len(matched) != 1:
            return None
        ((topic, covered),) = matched.items()
        if any(word not in covered and word not in _FILLERS for word in words):
            return None
        return topic

    @staticmethod
    def _contains(words: list[str], phrase: tuple[str, ...]) -> bool:
        size = len(phrase)
        return any(tuple(words[start : start + size]) == phrase for start in range(len(words) - size + 1))
